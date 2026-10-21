from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user
from ..models import Employee
from ..schemas import ChangePassword, EmployeeOut, Token
from ..security import create_access_token, hash_password, verify_password
from .employees import to_out

router = APIRouter(prefix="/api/auth", tags=["Xác thực"])


@router.post("/login", response_model=Token, summary="Đăng nhập (username = email)")
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(Employee).filter(Employee.email == form.username.strip().lower()).first()
    if not user or not verify_password(form.password, user.hashed_password):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Email hoặc mật khẩu không đúng")
    if user.status != "active":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Tài khoản đã bị khóa")
    return Token(access_token=create_access_token(user.id))


@router.get("/me", response_model=EmployeeOut, summary="Thông tin tài khoản hiện tại")
def me(user: Employee = Depends(get_current_user)):
    return to_out(user)


@router.post("/change-password", summary="Đổi mật khẩu")
def change_password(
    data: ChangePassword,
    user: Employee = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not verify_password(data.old_password, user.hashed_password):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Mật khẩu cũ không đúng")
    user.hashed_password = hash_password(data.new_password)
    db.commit()
    return {"message": "Đổi mật khẩu thành công"}
