from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user, require_roles, visible_employee_ids
from ..models import Department, Employee
from ..schemas import EmployeeCreate, EmployeeOut, EmployeeUpdate
from ..security import hash_password

router = APIRouter(prefix="/api/employees", tags=["Nhân viên"])


def to_out(emp: Employee) -> EmployeeOut:
    return EmployeeOut(
        id=emp.id,
        code=emp.code,
        full_name=emp.full_name,
        email=emp.email,
        role=emp.role,
        phone=emp.phone,
        gender=emp.gender,
        address=emp.address,
        position=emp.position,
        department_id=emp.department_id,
        manager_id=emp.manager_id,
        hire_date=emp.hire_date,
        status=emp.status,
        department_name=emp.department.name if emp.department else None,
        manager_name=emp.manager.full_name if emp.manager else None,
    )


def _validate_refs(db: Session, department_id, manager_id, self_id=None):
    if department_id is not None and not db.get(Department, department_id):
        raise HTTPException(400, "Phòng ban không tồn tại")
    if manager_id is not None:
        if self_id is not None and manager_id == self_id:
            raise HTTPException(400, "Nhân viên không thể tự quản lý chính mình")
        if not db.get(Employee, manager_id):
            raise HTTPException(400, "Người quản lý không tồn tại")


@router.get("", response_model=list[EmployeeOut], summary="Danh sách nhân viên")
def list_employees(
    q: Optional[str] = Query(None, description="Tìm theo tên, mã, email"),
    department_id: Optional[int] = None,
    status: Optional[str] = None,
    role: Optional[str] = None,
    db: Session = Depends(get_db),
    user: Employee = Depends(get_current_user),
):
    query = db.query(Employee)
    if q:
        like = f"%{q.strip()}%"
        query = query.filter(or_(Employee.full_name.ilike(like), Employee.code.ilike(like), Employee.email.ilike(like)))
    if department_id:
        query = query.filter(Employee.department_id == department_id)
    if status:
        query = query.filter(Employee.status == status)
    if role:
        query = query.filter(Employee.role == role)
    return [to_out(e) for e in query.order_by(Employee.code).all()]


@router.get("/team", response_model=list[EmployeeOut], summary="Nhân viên thuộc quyền quản lý của tôi")
def my_team(db: Session = Depends(get_db), user: Employee = Depends(get_current_user)):
    ids = visible_employee_ids(db, user)
    query = db.query(Employee)
    if ids is not None:
        query = query.filter(Employee.id.in_(ids))
    return [to_out(e) for e in query.order_by(Employee.code).all()]


@router.post("", response_model=EmployeeOut, status_code=201, dependencies=[Depends(require_roles("admin"))])
def create_employee(data: EmployeeCreate, db: Session = Depends(get_db)):
    email = data.email.lower()
    if db.query(Employee).filter(Employee.email == email).first():
        raise HTTPException(400, "Email đã được sử dụng")
    if db.query(Employee).filter(Employee.code == data.code).first():
        raise HTTPException(400, "Mã nhân viên đã tồn tại")
    _validate_refs(db, data.department_id, data.manager_id)
    values = data.model_dump(exclude={"password", "email"})
    emp = Employee(**values, email=email, hashed_password=hash_password(data.password))
    db.add(emp)
    db.commit()
    db.refresh(emp)
    return to_out(emp)


@router.get("/{emp_id}", response_model=EmployeeOut)
def get_employee(emp_id: int, db: Session = Depends(get_db), user: Employee = Depends(get_current_user)):
    emp = db.get(Employee, emp_id)
    if not emp:
        raise HTTPException(404, "Không tìm thấy nhân viên")
    return to_out(emp)


@router.put("/{emp_id}", response_model=EmployeeOut, dependencies=[Depends(require_roles("admin"))])
def update_employee(emp_id: int, data: EmployeeUpdate, db: Session = Depends(get_db)):
    emp = db.get(Employee, emp_id)
    if not emp:
        raise HTTPException(404, "Không tìm thấy nhân viên")
    values = data.model_dump(exclude_unset=True)
    if "email" in values and values["email"]:
        values["email"] = values["email"].lower()
        if db.query(Employee).filter(Employee.email == values["email"], Employee.id != emp_id).first():
            raise HTTPException(400, "Email đã được sử dụng")
    if "code" in values and db.query(Employee).filter(Employee.code == values["code"], Employee.id != emp_id).first():
        raise HTTPException(400, "Mã nhân viên đã tồn tại")
    _validate_refs(db, values.get("department_id"), values.get("manager_id"), self_id=emp_id)
    password = values.pop("password", None)
    if password:
        emp.hashed_password = hash_password(password)
    for key, value in values.items():
        setattr(emp, key, value)
    db.commit()
    db.refresh(emp)
    return to_out(emp)


@router.delete("/{emp_id}", summary="Vô hiệu hóa nhân viên (nghỉ việc)")
def deactivate_employee(emp_id: int, db: Session = Depends(get_db), user: Employee = Depends(require_roles("admin"))):
    emp = db.get(Employee, emp_id)
    if not emp:
        raise HTTPException(404, "Không tìm thấy nhân viên")
    if emp.id == user.id:
        raise HTTPException(400, "Không thể vô hiệu hóa chính tài khoản đang đăng nhập")
    emp.status = "inactive"
    db.commit()
    return {"message": "Đã vô hiệu hóa nhân viên (dữ liệu chấm công, báo cáo vẫn được giữ lại)"}
