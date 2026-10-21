from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user, require_roles, visible_employee_ids
from ..models import Employee, Task
from ..schemas import TaskCreate, TaskOut, TaskUpdate

router = APIRouter(prefix="/api/tasks", tags=["Công việc"])


def to_out(t: Task) -> TaskOut:
    return TaskOut(
        id=t.id,
        title=t.title,
        description=t.description,
        assignee_id=t.assignee_id,
        priority=t.priority,
        status=t.status,
        due_date=t.due_date,
        creator_id=t.creator_id,
        assignee_name=t.assignee.full_name if t.assignee else None,
        creator_name=t.creator.full_name if t.creator else None,
        created_at=t.created_at,
    )


@router.get("", response_model=list[TaskOut], summary="Danh sách công việc (theo phạm vi quản lý)")
def list_tasks(
    status: Optional[str] = None,
    assignee_id: Optional[int] = None,
    mine: bool = False,
    db: Session = Depends(get_db),
    user: Employee = Depends(get_current_user),
):
    query = db.query(Task)
    if mine:
        query = query.filter(Task.assignee_id == user.id)
    else:
        ids = visible_employee_ids(db, user)
        if ids is not None:
            query = query.filter(or_(Task.assignee_id.in_(ids), Task.creator_id == user.id))
    if status:
        query = query.filter(Task.status == status)
    if assignee_id:
        query = query.filter(Task.assignee_id == assignee_id)
    return [to_out(t) for t in query.order_by(Task.created_at.desc()).all()]


@router.post("", response_model=TaskOut, status_code=201, summary="Giao việc (admin/quản lý)")
def create_task(
    data: TaskCreate,
    db: Session = Depends(get_db),
    user: Employee = Depends(require_roles("admin", "manager")),
):
    if data.assignee_id is not None:
        ids = visible_employee_ids(db, user)
        if not db.get(Employee, data.assignee_id):
            raise HTTPException(400, "Người được giao không tồn tại")
        if ids is not None and data.assignee_id not in ids:
            raise HTTPException(403, "Chỉ được giao việc cho nhân viên thuộc quyền quản lý")
    task = Task(**data.model_dump(), creator_id=user.id)
    db.add(task)
    db.commit()
    db.refresh(task)
    return to_out(task)


@router.get("/{task_id}", response_model=TaskOut)
def get_task(task_id: int, db: Session = Depends(get_db), user: Employee = Depends(get_current_user)):
    task = db.get(Task, task_id)
    if not task:
        raise HTTPException(404, "Không tìm thấy công việc")
    return to_out(task)


@router.put("/{task_id}", response_model=TaskOut, summary="Cập nhật công việc")
def update_task(task_id: int, data: TaskUpdate, db: Session = Depends(get_db), user: Employee = Depends(get_current_user)):
    task = db.get(Task, task_id)
    if not task:
        raise HTTPException(404, "Không tìm thấy công việc")
    values = data.model_dump(exclude_unset=True)
    is_manager_side = user.role == "admin" or task.creator_id == user.id
    if user.role == "manager" and not is_manager_side:
        ids = visible_employee_ids(db, user) or []
        is_manager_side = task.assignee_id in ids
    if not is_manager_side:
        # Người được giao chỉ được đổi trạng thái
        if task.assignee_id != user.id:
            raise HTTPException(403, "Bạn không có quyền cập nhật công việc này")
        if set(values) - {"status"}:
            raise HTTPException(403, "Bạn chỉ được cập nhật trạng thái công việc được giao")
    if values.get("assignee_id") and not db.get(Employee, values["assignee_id"]):
        raise HTTPException(400, "Người được giao không tồn tại")
    for key, value in values.items():
        setattr(task, key, value)
    db.commit()
    db.refresh(task)
    return to_out(task)


@router.delete("/{task_id}")
def delete_task(task_id: int, db: Session = Depends(get_db), user: Employee = Depends(require_roles("admin", "manager"))):
    task = db.get(Task, task_id)
    if not task:
        raise HTTPException(404, "Không tìm thấy công việc")
    if user.role != "admin" and task.creator_id != user.id:
        raise HTTPException(403, "Chỉ người giao việc hoặc admin mới được xóa")
    db.delete(task)
    db.commit()
    return {"message": "Đã xóa công việc"}
