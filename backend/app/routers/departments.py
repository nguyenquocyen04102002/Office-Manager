from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user, require_roles
from ..models import Department, Employee
from ..schemas import DepartmentCreate, DepartmentOut, DepartmentUpdate

router = APIRouter(prefix="/api/departments", tags=["Phòng ban"])


def _out(db: Session, dep: Department) -> DepartmentOut:
    count = (
        db.query(func.count(Employee.id))
        .filter(Employee.department_id == dep.id, Employee.status == "active")
        .scalar()
    )
    return DepartmentOut(id=dep.id, name=dep.name, description=dep.description, employee_count=count or 0)


@router.get("", response_model=list[DepartmentOut], dependencies=[Depends(get_current_user)])
def list_departments(db: Session = Depends(get_db)):
    return [_out(db, d) for d in db.query(Department).order_by(Department.name).all()]


@router.post("", response_model=DepartmentOut, status_code=201, dependencies=[Depends(require_roles("admin"))])
def create_department(data: DepartmentCreate, db: Session = Depends(get_db)):
    if db.query(Department).filter(Department.name == data.name).first():
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Tên phòng ban đã tồn tại")
    dep = Department(**data.model_dump())
    db.add(dep)
    db.commit()
    db.refresh(dep)
    return _out(db, dep)


@router.get("/{dep_id}", response_model=DepartmentOut, dependencies=[Depends(get_current_user)])
def get_department(dep_id: int, db: Session = Depends(get_db)):
    dep = db.get(Department, dep_id)
    if not dep:
        raise HTTPException(404, "Không tìm thấy phòng ban")
    return _out(db, dep)


@router.put("/{dep_id}", response_model=DepartmentOut, dependencies=[Depends(require_roles("admin"))])
def update_department(dep_id: int, data: DepartmentUpdate, db: Session = Depends(get_db)):
    dep = db.get(Department, dep_id)
    if not dep:
        raise HTTPException(404, "Không tìm thấy phòng ban")
    values = data.model_dump(exclude_unset=True)
    if "name" in values and db.query(Department).filter(Department.name == values["name"], Department.id != dep_id).first():
        raise HTTPException(400, "Tên phòng ban đã tồn tại")
    for key, value in values.items():
        setattr(dep, key, value)
    db.commit()
    db.refresh(dep)
    return _out(db, dep)


@router.delete("/{dep_id}", dependencies=[Depends(require_roles("admin"))])
def delete_department(dep_id: int, db: Session = Depends(get_db)):
    dep = db.get(Department, dep_id)
    if not dep:
        raise HTTPException(404, "Không tìm thấy phòng ban")
    # Nhân viên thuộc phòng ban sẽ được chuyển về "chưa phân phòng"
    db.query(Employee).filter(Employee.department_id == dep_id).update({Employee.department_id: None})
    db.delete(dep)
    db.commit()
    return {"message": "Đã xóa phòng ban"}
