import csv
import io
from calendar import monthrange
from datetime import date, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import now_local, require_roles, visible_employee_ids
from ..models import Asset, Attendance, Department, Employee, LeaveRequest, Task

router = APIRouter(prefix="/api/reports", tags=["Báo cáo"])
manage = require_roles("admin", "manager")


def _workdays_in_month(year: int, month: int, until: Optional[date] = None) -> int:
    last = monthrange(year, month)[1]
    end = date(year, month, last)
    if until and until < end:
        end = until
    cur, count = date(year, month, 1), 0
    while cur <= end:
        if cur.weekday() < 5:
            count += 1
        cur += timedelta(days=1)
    return count


def monthly_rows(db: Session, user: Employee, year: int, month: int, department_id: Optional[int]) -> list[dict]:
    query = db.query(Employee).filter(Employee.status == "active")
    ids = visible_employee_ids(db, user)
    if ids is not None:
        query = query.filter(Employee.id.in_(ids))
    if department_id:
        query = query.filter(Employee.department_id == department_id)
    employees = query.order_by(Employee.code).all()

    first, last = date(year, month, 1), date(year, month, monthrange(year, month)[1])
    today = now_local().date()
    workdays = _workdays_in_month(year, month, until=today if (year, month) == (today.year, today.month) else None)

    records = (
        db.query(Attendance)
        .filter(Attendance.work_date >= first, Attendance.work_date <= last)
        .filter(Attendance.employee_id.in_([e.id for e in employees] or [0]))
        .all()
    )
    by_emp: dict[int, list[Attendance]] = {}
    for r in records:
        by_emp.setdefault(r.employee_id, []).append(r)

    rows = []
    for e in employees:
        recs = by_emp.get(e.id, [])
        worked = [r for r in recs if r.check_in]
        late = sum(1 for r in recs if r.status in ("late", "late_early"))
        early = sum(1 for r in recs if r.status in ("early_leave", "late_early"))
        leave = sum(1 for r in recs if r.status == "leave")
        hours = sum(
            (r.check_out - r.check_in).total_seconds() / 3600 for r in worked if r.check_out and r.check_out > r.check_in
        )
        rows.append(
            {
                "employee_id": e.id,
                "code": e.code,
                "full_name": e.full_name,
                "department": e.department.name if e.department else "",
                "workdays": workdays,
                "days_worked": len(worked),
                "late": late,
                "early_leave": early,
                "leave": leave,
                "absent": max(workdays - len(worked) - leave, 0),
                "total_hours": round(hours, 1),
            }
        )
    return rows


@router.get("/attendance-monthly", summary="Báo cáo chấm công theo tháng")
def attendance_monthly(
    year: int = Query(default=None),
    month: int = Query(default=None, ge=1, le=12),
    department_id: Optional[int] = None,
    db: Session = Depends(get_db),
    user: Employee = Depends(manage),
):
    today = now_local().date()
    year, month = year or today.year, month or today.month
    return {"year": year, "month": month, "rows": monthly_rows(db, user, year, month, department_id)}


@router.get("/attendance-monthly/export", summary="Xuất báo cáo chấm công ra CSV (mở được bằng Excel)")
def attendance_monthly_export(
    year: int = Query(default=None),
    month: int = Query(default=None, ge=1, le=12),
    department_id: Optional[int] = None,
    db: Session = Depends(get_db),
    user: Employee = Depends(manage),
):
    today = now_local().date()
    year, month = year or today.year, month or today.month
    rows = monthly_rows(db, user, year, month, department_id)

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        ["Mã NV", "Họ tên", "Phòng ban", "Ngày công chuẩn", "Ngày đi làm", "Đi muộn", "Về sớm", "Nghỉ phép", "Vắng", "Tổng giờ"]
    )
    for r in rows:
        writer.writerow(
            [r["code"], r["full_name"], r["department"], r["workdays"], r["days_worked"], r["late"], r["early_leave"], r["leave"], r["absent"], r["total_hours"]]
        )
    # utf-8-sig để Excel hiển thị đúng tiếng Việt
    data = buffer.getvalue().encode("utf-8-sig")
    filename = f"bao-cao-cham-cong-{year}-{month:02d}.csv"
    return StreamingResponse(
        iter([data]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/overview", summary="Báo cáo tổng quan tổ chức")
def overview(db: Session = Depends(get_db), user: Employee = Depends(manage)):
    by_dept = (
        db.query(Department.name, func.count(Employee.id))
        .outerjoin(Employee, (Employee.department_id == Department.id) & (Employee.status == "active"))
        .group_by(Department.name)
        .order_by(Department.name)
        .all()
    )
    ids = visible_employee_ids(db, user)

    def count_by(model, column, extra=None):
        q = db.query(column, func.count(model.id))
        if extra is not None:
            q = q.filter(extra)
        return {k: v for k, v in q.group_by(column).all()}

    task_q = db.query(Task.status, func.count(Task.id))
    leave_q = db.query(LeaveRequest.status, func.count(LeaveRequest.id))
    if ids is not None:
        task_q = task_q.filter(Task.assignee_id.in_(ids))
        leave_q = leave_q.filter(LeaveRequest.employee_id.in_(ids))
    return {
        "employees_by_department": [{"department": n, "count": c} for n, c in by_dept],
        "employees_by_role": count_by(Employee, Employee.role, Employee.status == "active"),
        "tasks_by_status": {k: v for k, v in task_q.group_by(Task.status).all()},
        "leaves_by_status": {k: v for k, v in leave_q.group_by(LeaveRequest.status).all()},
        "assets_by_status": count_by(Asset, Asset.status),
    }
