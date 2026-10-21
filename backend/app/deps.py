from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from .config import settings
from .database import get_db
from .models import Employee
from .security import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def now_local() -> datetime:
    """Thời gian hiện tại theo múi giờ cấu hình, trả về dạng naive."""
    return datetime.now(ZoneInfo(settings.TIMEZONE)).replace(tzinfo=None)


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> Employee:
    user_id = decode_access_token(token)
    if user_id is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Phiên đăng nhập không hợp lệ hoặc đã hết hạn")
    user = db.get(Employee, user_id)
    if not user or user.status != "active":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Tài khoản không tồn tại hoặc đã bị khóa")
    return user


def require_roles(*roles: str):
    def checker(user: Employee = Depends(get_current_user)) -> Employee:
        if user.role not in roles:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Bạn không có quyền thực hiện thao tác này")
        return user

    return checker


def visible_employee_ids(db: Session, user: Employee) -> list[int] | None:
    """Danh sách nhân viên mà user được xem dữ liệu.

    - admin   : None (xem tất cả)
    - manager : bản thân + toàn bộ cấp dưới (đệ quy)
    - employee: chỉ bản thân
    """
    if user.role == "admin":
        return None
    ids = {user.id}
    if user.role == "manager":
        frontier = {user.id}
        while frontier:
            rows = db.query(Employee.id).filter(Employee.manager_id.in_(frontier)).all()
            frontier = {r[0] for r in rows} - ids
            ids |= frontier
    return list(ids)


def can_access_employee(db: Session, user: Employee, employee_id: int) -> bool:
    ids = visible_employee_ids(db, user)
    return ids is None or employee_id in ids
