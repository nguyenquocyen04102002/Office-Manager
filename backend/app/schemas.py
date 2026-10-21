from datetime import date, datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field

Role = Literal["admin", "manager", "employee"]


class ORM(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# ---------- Auth ----------
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class ChangePassword(BaseModel):
    old_password: str
    new_password: str = Field(min_length=6, max_length=72)


# ---------- Department ----------
class DepartmentBase(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: Optional[str] = None


class DepartmentCreate(DepartmentBase):
    pass


class DepartmentUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=120)
    description: Optional[str] = None


class DepartmentOut(ORM, DepartmentBase):
    id: int
    employee_count: int = 0


# ---------- Employee ----------
class EmployeeBase(BaseModel):
    code: str = Field(min_length=1, max_length=30)
    full_name: str = Field(min_length=1, max_length=150)
    email: EmailStr
    role: Role = "employee"
    phone: Optional[str] = None
    gender: Optional[str] = None
    address: Optional[str] = None
    position: Optional[str] = None
    department_id: Optional[int] = None
    manager_id: Optional[int] = None
    hire_date: Optional[date] = None
    status: Literal["active", "inactive"] = "active"


class EmployeeCreate(EmployeeBase):
    password: str = Field(min_length=6, max_length=72)


class EmployeeUpdate(BaseModel):
    code: Optional[str] = Field(default=None, min_length=1, max_length=30)
    full_name: Optional[str] = Field(default=None, min_length=1, max_length=150)
    email: Optional[EmailStr] = None
    role: Optional[Role] = None
    phone: Optional[str] = None
    gender: Optional[str] = None
    address: Optional[str] = None
    position: Optional[str] = None
    department_id: Optional[int] = None
    manager_id: Optional[int] = None
    hire_date: Optional[date] = None
    status: Optional[Literal["active", "inactive"]] = None
    password: Optional[str] = Field(default=None, min_length=6, max_length=72)


class EmployeeOut(ORM, EmployeeBase):
    id: int
    department_name: Optional[str] = None
    manager_name: Optional[str] = None


# ---------- Attendance ----------
class AttendanceOut(ORM):
    id: int
    employee_id: int
    employee_name: Optional[str] = None
    employee_code: Optional[str] = None
    work_date: date
    check_in: Optional[datetime] = None
    check_out: Optional[datetime] = None
    status: str
    note: Optional[str] = None


class AttendanceUpdate(BaseModel):
    check_in: Optional[datetime] = None
    check_out: Optional[datetime] = None
    status: Optional[Literal["present", "late", "early_leave", "late_early", "leave", "absent"]] = None
    note: Optional[str] = None


class AttendanceManual(AttendanceUpdate):
    employee_id: int
    work_date: date


class CheckNote(BaseModel):
    note: Optional[str] = None


# ---------- Leave ----------
LeaveType = Literal["annual", "sick", "unpaid", "maternity", "other"]


class LeaveCreate(BaseModel):
    leave_type: LeaveType = "annual"
    start_date: date
    end_date: date
    reason: Optional[str] = None


class LeaveReview(BaseModel):
    approve: bool
    review_note: Optional[str] = None


class LeaveOut(ORM):
    id: int
    employee_id: int
    employee_name: Optional[str] = None
    leave_type: str
    start_date: date
    end_date: date
    days: float
    reason: Optional[str] = None
    status: str
    reviewer_id: Optional[int] = None
    reviewer_name: Optional[str] = None
    review_note: Optional[str] = None
    created_at: datetime


# ---------- Task ----------
class TaskBase(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: Optional[str] = None
    assignee_id: Optional[int] = None
    priority: Literal["low", "medium", "high"] = "medium"
    status: Literal["todo", "in_progress", "done"] = "todo"
    due_date: Optional[date] = None


class TaskCreate(TaskBase):
    pass


class TaskUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    description: Optional[str] = None
    assignee_id: Optional[int] = None
    priority: Optional[Literal["low", "medium", "high"]] = None
    status: Optional[Literal["todo", "in_progress", "done"]] = None
    due_date: Optional[date] = None


class TaskOut(ORM, TaskBase):
    id: int
    creator_id: Optional[int] = None
    assignee_name: Optional[str] = None
    creator_name: Optional[str] = None
    created_at: datetime


# ---------- Asset ----------
AssetStatus = Literal["available", "in_use", "maintenance", "retired"]


class AssetBase(BaseModel):
    code: str = Field(min_length=1, max_length=40)
    name: str = Field(min_length=1, max_length=150)
    category: Optional[str] = None
    status: AssetStatus = "available"
    assigned_to_id: Optional[int] = None
    purchase_date: Optional[date] = None
    note: Optional[str] = None


class AssetCreate(AssetBase):
    pass


class AssetUpdate(BaseModel):
    code: Optional[str] = Field(default=None, min_length=1, max_length=40)
    name: Optional[str] = Field(default=None, min_length=1, max_length=150)
    category: Optional[str] = None
    status: Optional[AssetStatus] = None
    assigned_to_id: Optional[int] = None
    purchase_date: Optional[date] = None
    note: Optional[str] = None


class AssetOut(ORM, AssetBase):
    id: int
    assigned_to_name: Optional[str] = None


# ---------- Room & Booking ----------
class RoomBase(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    capacity: int = Field(default=4, ge=1)
    location: Optional[str] = None
    equipment: Optional[str] = None


class RoomCreate(RoomBase):
    pass


class RoomUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    capacity: Optional[int] = Field(default=None, ge=1)
    location: Optional[str] = None
    equipment: Optional[str] = None


class RoomOut(ORM, RoomBase):
    id: int


class BookingCreate(BaseModel):
    room_id: int
    title: str = Field(min_length=1, max_length=200)
    start_time: datetime
    end_time: datetime


class BookingOut(ORM):
    id: int
    room_id: int
    room_name: Optional[str] = None
    employee_id: int
    employee_name: Optional[str] = None
    title: str
    start_time: datetime
    end_time: datetime


# ---------- Announcement ----------
class AnnouncementCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1)
    pinned: bool = False


class AnnouncementUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    content: Optional[str] = None
    pinned: Optional[bool] = None


class AnnouncementOut(ORM):
    id: int
    title: str
    content: str
    pinned: bool
    author_id: Optional[int] = None
    author_name: Optional[str] = None
    created_at: datetime
