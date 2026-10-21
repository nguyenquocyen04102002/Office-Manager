from datetime import timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user, now_local, require_roles, visible_employee_ids
from ..models import Attendance, Employee, LeaveRequest
from ..schemas import LeaveCreate, LeaveOut, LeaveReview

router = APIRouter(prefix="/api/leaves", tags=["Nghỉ phép"])


def to_out(l: LeaveRequest) -> LeaveOut:
    return LeaveOut(
        id=l.id,
        employee_id=l.employee_id,
        employee_name=l.employee.full_name if l.employee else None,
        leave_type=l.leave_type,
        start_date=l.start_date,
        end_date=l.end_date,
        days=float(l.days),
        reason=l.reason,
        status=l.status,
        reviewer_id=l.reviewer_id,
        reviewer_name=l.reviewer.full_name if l.reviewer else None,
        review_note=l.review_note,
        created_at=l.created_at,
    )


def count_workdays(start, end) -> int:
    days, cur = 0, start
    while cur <= end:
        if cur.weekday() < 5:
            days += 1
        cur += timedelta(days=1)
    return days


@router.post("", response_model=LeaveOut, status_code=201, summary="Gửi đơn xin nghỉ phép")
def create_leave(data: LeaveCreate, db: Session = Depends(get_db), user: Employee = Depends(get_current_user)):
    if data.end_date < data.start_date:
        raise HTTPException(400, "Ngày kết thúc phải sau hoặc bằng ngày bắt đầu")
    days = count_workdays(data.start_date, data.end_date)
    if days == 0:
        raise HTTPException(400, "Khoảng thời gian chọn không có ngày làm việc nào (T2-T6)")
    overlap = (
        db.query(LeaveRequest)
        .filter(
            LeaveRequest.employee_id == user.id,
            LeaveRequest.status.in_(["pending", "approved"]),
            LeaveRequest.start_date <= data.end_date,
            LeaveRequest.end_date >= data.start_date,
        )
        .first()
    )
    if overlap:
        raise HTTPException(400, "Bạn đã có đơn nghỉ phép trùng thời gian này")
    leave = LeaveRequest(employee_id=user.id, days=days, **data.model_dump())
    db.add(leave)
    db.commit()
    db.refresh(leave)
    return to_out(leave)


@router.get("", response_model=list[LeaveOut], summary="Danh sách đơn nghỉ phép (theo phạm vi quản lý)")
def list_leaves(
    status: Optional[str] = None,
    mine: bool = False,
    db: Session = Depends(get_db),
    user: Employee = Depends(get_current_user),
):
    query = db.query(LeaveRequest)
    if mine:
        query = query.filter(LeaveRequest.employee_id == user.id)
    else:
        ids = visible_employee_ids(db, user)
        if ids is not None:
            query = query.filter(LeaveRequest.employee_id.in_(ids))
    if status:
        query = query.filter(LeaveRequest.status == status)
    return [to_out(l) for l in query.order_by(LeaveRequest.created_at.desc()).all()]


@router.put("/{leave_id}/review", response_model=LeaveOut, summary="Duyệt / từ chối đơn")
def review_leave(
    leave_id: int,
    data: LeaveReview,
    db: Session = Depends(get_db),
    user: Employee = Depends(require_roles("admin", "manager")),
):
    leave = db.get(LeaveRequest, leave_id)
    if not leave:
        raise HTTPException(404, "Không tìm thấy đơn nghỉ phép")
    if leave.status != "pending":
        raise HTTPException(400, "Đơn này đã được xử lý")
    ids = visible_employee_ids(db, user)
    if ids is not None and leave.employee_id not in ids:
        raise HTTPException(403, "Nhân viên không thuộc quyền quản lý của bạn")
    if leave.employee_id == user.id and user.role != "admin":
        raise HTTPException(403, "Bạn không thể tự duyệt đơn của mình")

    leave.status = "approved" if data.approve else "rejected"
    leave.reviewer_id = user.id
    leave.review_note = data.review_note

    if data.approve:
        # Ghi nhận các ngày nghỉ vào bảng chấm công
        cur = leave.start_date
        while cur <= leave.end_date:
            if cur.weekday() < 5:
                record = (
                    db.query(Attendance)
                    .filter(Attendance.employee_id == leave.employee_id, Attendance.work_date == cur)
                    .first()
                )
                if record is None:
                    db.add(Attendance(employee_id=leave.employee_id, work_date=cur, status="leave", note="Nghỉ phép"))
                elif not record.check_in:
                    record.status = "leave"
                    record.note = "Nghỉ phép"
            cur += timedelta(days=1)
    db.commit()
    db.refresh(leave)
    return to_out(leave)


@router.delete("/{leave_id}", summary="Hủy đơn đang chờ duyệt")
def cancel_leave(leave_id: int, db: Session = Depends(get_db), user: Employee = Depends(get_current_user)):
    leave = db.get(LeaveRequest, leave_id)
    if not leave:
        raise HTTPException(404, "Không tìm thấy đơn nghỉ phép")
    if leave.employee_id != user.id and user.role != "admin":
        raise HTTPException(403, "Bạn chỉ có thể hủy đơn của chính mình")
    if leave.status != "pending":
        raise HTTPException(400, "Chỉ có thể hủy đơn đang chờ duyệt")
    db.delete(leave)
    db.commit()
    return {"message": "Đã hủy đơn nghỉ phép"}
