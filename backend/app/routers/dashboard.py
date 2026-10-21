from datetime import datetime, time, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user, now_local, visible_employee_ids
from ..models import Announcement, Asset, Attendance, Booking, Department, Employee, LeaveRequest, Task

router = APIRouter(prefix="/api/dashboard", tags=["Tổng quan"])


@router.get("/stats", summary="Số liệu tổng quan cho trang chủ")
def stats(db: Session = Depends(get_db), user: Employee = Depends(get_current_user)):
    now = now_local()
    today = now.date()
    ids = visible_employee_ids(db, user)

    emp_q = db.query(func.count(Employee.id)).filter(Employee.status == "active")
    att_q = db.query(Attendance).filter(Attendance.work_date == today)
    leave_q = db.query(func.count(LeaveRequest.id)).filter(LeaveRequest.status == "pending")
    task_q = db.query(func.count(Task.id)).filter(Task.status != "done")
    if ids is not None:
        emp_q = emp_q.filter(Employee.id.in_(ids))
        att_q = att_q.filter(Attendance.employee_id.in_(ids))
        leave_q = leave_q.filter(LeaveRequest.employee_id.in_(ids))
        task_q = task_q.filter(Task.assignee_id.in_(ids))
    # Nhân viên thường chỉ thấy đơn đang chờ của chính mình
    if user.role == "employee":
        leave_q = db.query(func.count(LeaveRequest.id)).filter(
            LeaveRequest.status == "pending", LeaveRequest.employee_id == user.id
        )

    today_records = att_q.all()
    day_start = datetime.combine(today, time.min)
    bookings_today = (
        db.query(func.count(Booking.id))
        .filter(Booking.start_time >= day_start, Booking.start_time < day_start + timedelta(days=1))
        .scalar()
    )
    my_open_tasks = (
        db.query(func.count(Task.id)).filter(Task.assignee_id == user.id, Task.status != "done").scalar()
    )
    assets_available = db.query(func.count(Asset.id)).filter(Asset.status == "available").scalar()
    latest = db.query(Announcement).order_by(Announcement.pinned.desc(), Announcement.created_at.desc()).limit(3).all()

    return {
        "scope": "all" if ids is None else ("team" if user.role == "manager" else "me"),
        "total_employees": emp_q.scalar() or 0,
        "total_departments": db.query(func.count(Department.id)).scalar() or 0,
        "present_today": sum(1 for r in today_records if r.check_in),
        "late_today": sum(1 for r in today_records if r.status in ("late", "late_early")),
        "on_leave_today": sum(1 for r in today_records if r.status == "leave"),
        "pending_leaves": leave_q.scalar() or 0,
        "open_tasks": task_q.scalar() or 0,
        "my_open_tasks": my_open_tasks or 0,
        "bookings_today": bookings_today or 0,
        "assets_available": assets_available or 0,
        "announcements": [
            {"id": a.id, "title": a.title, "content": a.content, "pinned": a.pinned, "created_at": a.created_at}
            for a in latest
        ],
    }
