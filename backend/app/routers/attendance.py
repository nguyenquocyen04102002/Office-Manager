from datetime import date, datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..config import settings
from ..database import get_db
from ..deps import get_current_user, now_local, require_roles, visible_employee_ids
from ..models import Attendance, Employee
from ..schemas import AttendanceManual, AttendanceOut, AttendanceUpdate, CheckNote

router = APIRouter(prefix="/api/attendance", tags=["Điểm danh"])


def to_out(a: Attendance) -> AttendanceOut:
    return AttendanceOut(
        id=a.id,
        employee_id=a.employee_id,
        employee_name=a.employee.full_name if a.employee else None,
        employee_code=a.employee.code if a.employee else None,
        work_date=a.work_date,
        check_in=a.check_in,
        check_out=a.check_out,
        status=a.status,
        note=a.note,
    )


def compute_status(check_in: Optional[datetime], check_out: Optional[datetime], current: str = "present") -> str:
    """Tính trạng thái từ giờ vào/ra theo giờ làm việc cấu hình."""
    if current in ("leave", "absent") and not check_in:
        return current
    if not check_in:
        return current
    late = check_in.time() > settings.WORK_START
    early = bool(check_out) and check_out.time() < settings.WORK_END
    if late and early:
        return "late_early"
    if late:
        return "late"
    if early:
        return "early_leave"
    return "present"


@router.post("/check-in", response_model=AttendanceOut, summary="Điểm danh vào ca")
def check_in(data: CheckNote = CheckNote(), db: Session = Depends(get_db), user: Employee = Depends(get_current_user)):
    now = now_local()
    record = (
        db.query(Attendance)
        .filter(Attendance.employee_id == user.id, Attendance.work_date == now.date())
        .first()
    )
    if record and record.check_in:
        raise HTTPException(400, "Hôm nay bạn đã điểm danh vào ca rồi")
    if not record:
        record = Attendance(employee_id=user.id, work_date=now.date())
        db.add(record)
    record.check_in = now
    record.note = data.note or record.note
    record.status = compute_status(now, None)
    db.commit()
    db.refresh(record)
    return to_out(record)


@router.post("/check-out", response_model=AttendanceOut, summary="Điểm danh ra về")
def check_out(data: CheckNote = CheckNote(), db: Session = Depends(get_db), user: Employee = Depends(get_current_user)):
    now = now_local()
    record = (
        db.query(Attendance)
        .filter(Attendance.employee_id == user.id, Attendance.work_date == now.date())
        .first()
    )
    if not record or not record.check_in:
        raise HTTPException(400, "Bạn chưa điểm danh vào ca hôm nay")
    if record.check_out:
        raise HTTPException(400, "Hôm nay bạn đã điểm danh ra về rồi")
    record.check_out = now
    if data.note:
        record.note = data.note
    record.status = compute_status(record.check_in, now)
    db.commit()
    db.refresh(record)
    return to_out(record)


@router.get("/today", response_model=Optional[AttendanceOut], summary="Trạng thái điểm danh hôm nay của tôi")
def today(db: Session = Depends(get_db), user: Employee = Depends(get_current_user)):
    record = (
        db.query(Attendance)
        .filter(Attendance.employee_id == user.id, Attendance.work_date == now_local().date())
        .first()
    )
    return to_out(record) if record else None


@router.get("", response_model=list[AttendanceOut], summary="Lịch sử điểm danh (theo phạm vi quản lý)")
def list_attendance(
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    employee_id: Optional[int] = None,
    department_id: Optional[int] = None,
    status: Optional[str] = None,
    limit: int = Query(500, le=2000),
    db: Session = Depends(get_db),
    user: Employee = Depends(get_current_user),
):
    query = db.query(Attendance).join(Employee, Employee.id == Attendance.employee_id)
    ids = visible_employee_ids(db, user)
    if ids is not None:
        query = query.filter(Attendance.employee_id.in_(ids))
    if employee_id:
        query = query.filter(Attendance.employee_id == employee_id)
    if department_id:
        query = query.filter(Employee.department_id == department_id)
    if date_from:
        query = query.filter(Attendance.work_date >= date_from)
    if date_to:
        query = query.filter(Attendance.work_date <= date_to)
    if status:
        query = query.filter(Attendance.status == status)
    rows = query.order_by(Attendance.work_date.desc(), Employee.code).limit(limit).all()
    return [to_out(a) for a in rows]


@router.post("", response_model=AttendanceOut, status_code=201, summary="Admin/Quản lý: chấm công thủ công")
def manual_attendance(
    data: AttendanceManual,
    db: Session = Depends(get_db),
    user: Employee = Depends(require_roles("admin", "manager")),
):
    ids = visible_employee_ids(db, user)
    if ids is not None and data.employee_id not in ids:
        raise HTTPException(403, "Nhân viên không thuộc quyền quản lý của bạn")
    if not db.get(Employee, data.employee_id):
        raise HTTPException(400, "Nhân viên không tồn tại")
    if db.query(Attendance).filter(Attendance.employee_id == data.employee_id, Attendance.work_date == data.work_date).first():
        raise HTTPException(400, "Ngày này đã có bản ghi chấm công, hãy dùng chức năng sửa")
    record = Attendance(
        employee_id=data.employee_id,
        work_date=data.work_date,
        check_in=data.check_in,
        check_out=data.check_out,
        note=data.note,
        status=data.status or "present",
    )
    if not data.status:
        record.status = compute_status(record.check_in, record.check_out)
    db.add(record)
    db.commit()
    db.refresh(record)
    return to_out(record)


@router.put("/{att_id}", response_model=AttendanceOut, summary="Admin/Quản lý: sửa bản ghi chấm công")
def update_attendance(
    att_id: int,
    data: AttendanceUpdate,
    db: Session = Depends(get_db),
    user: Employee = Depends(require_roles("admin", "manager")),
):
    record = db.get(Attendance, att_id)
    if not record:
        raise HTTPException(404, "Không tìm thấy bản ghi chấm công")
    ids = visible_employee_ids(db, user)
    if ids is not None and record.employee_id not in ids:
        raise HTTPException(403, "Nhân viên không thuộc quyền quản lý của bạn")
    values = data.model_dump(exclude_unset=True)
    if values.get("status") is None:
        values.pop("status", None)  # bỏ trống -> tự tính lại theo giờ vào/ra
    for key, value in values.items():
        setattr(record, key, value)
    if "status" not in values:
        record.status = compute_status(record.check_in, record.check_out, record.status)
    db.commit()
    db.refresh(record)
    return to_out(record)


@router.delete("/{att_id}", summary="Admin: xóa bản ghi chấm công")
def delete_attendance(att_id: int, db: Session = Depends(get_db), user: Employee = Depends(require_roles("admin"))):
    record = db.get(Attendance, att_id)
    if not record:
        raise HTTPException(404, "Không tìm thấy bản ghi chấm công")
    db.delete(record)
    db.commit()
    return {"message": "Đã xóa bản ghi chấm công"}
