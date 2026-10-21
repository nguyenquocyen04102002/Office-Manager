from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from .database import Base


class Department(Base):
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True)
    name = Column(String(120), nullable=False, unique=True)
    description = Column(Text)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    employees = relationship("Employee", back_populates="department")


class Employee(Base):
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True)
    code = Column(String(30), nullable=False, unique=True)
    full_name = Column(String(150), nullable=False)
    email = Column(String(190), nullable=False, unique=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, default="employee")  # admin | manager | employee
    phone = Column(String(30))
    gender = Column(String(10))
    address = Column(String(255))
    position = Column(String(120))
    department_id = Column(Integer, ForeignKey("departments.id", ondelete="SET NULL"), index=True)
    manager_id = Column(Integer, ForeignKey("employees.id", ondelete="SET NULL"), index=True)
    hire_date = Column(Date)
    status = Column(String(20), nullable=False, default="active")  # active | inactive
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    department = relationship("Department", back_populates="employees")
    manager = relationship("Employee", remote_side=[id], backref="subordinates")


class Attendance(Base):
    __tablename__ = "attendances"
    __table_args__ = (UniqueConstraint("employee_id", "work_date", name="uq_attendance_employee_date"),)

    id = Column(Integer, primary_key=True)
    employee_id = Column(Integer, ForeignKey("employees.id", ondelete="CASCADE"), nullable=False)
    work_date = Column(Date, nullable=False, index=True)
    check_in = Column(DateTime)
    check_out = Column(DateTime)
    # present | late | early_leave | late_early | leave | absent
    status = Column(String(20), nullable=False, default="present")
    note = Column(String(255))

    employee = relationship("Employee")


class LeaveRequest(Base):
    __tablename__ = "leave_requests"
    __table_args__ = (CheckConstraint("end_date >= start_date", name="ck_leave_dates"),)

    id = Column(Integer, primary_key=True)
    employee_id = Column(Integer, ForeignKey("employees.id", ondelete="CASCADE"), nullable=False)
    leave_type = Column(String(30), nullable=False, default="annual")
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    days = Column(Numeric(5, 1), nullable=False, default=1)
    reason = Column(Text)
    status = Column(String(20), nullable=False, default="pending")  # pending | approved | rejected
    reviewer_id = Column(Integer, ForeignKey("employees.id", ondelete="SET NULL"))
    review_note = Column(String(255))
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    employee = relationship("Employee", foreign_keys=[employee_id])
    reviewer = relationship("Employee", foreign_keys=[reviewer_id])


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    assignee_id = Column(Integer, ForeignKey("employees.id", ondelete="SET NULL"))
    creator_id = Column(Integer, ForeignKey("employees.id", ondelete="SET NULL"))
    priority = Column(String(20), nullable=False, default="medium")  # low | medium | high
    status = Column(String(20), nullable=False, default="todo")  # todo | in_progress | done
    due_date = Column(Date)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    assignee = relationship("Employee", foreign_keys=[assignee_id])
    creator = relationship("Employee", foreign_keys=[creator_id])


class Asset(Base):
    __tablename__ = "assets"

    id = Column(Integer, primary_key=True)
    code = Column(String(40), nullable=False, unique=True)
    name = Column(String(150), nullable=False)
    category = Column(String(80))
    status = Column(String(20), nullable=False, default="available")  # available | in_use | maintenance | retired
    assigned_to_id = Column(Integer, ForeignKey("employees.id", ondelete="SET NULL"))
    purchase_date = Column(Date)
    note = Column(String(255))

    assigned_to = relationship("Employee")


class Room(Base):
    __tablename__ = "rooms"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    capacity = Column(Integer, nullable=False, default=4)
    location = Column(String(150))
    equipment = Column(String(255))


class Booking(Base):
    __tablename__ = "bookings"
    __table_args__ = (CheckConstraint("end_time > start_time", name="ck_booking_time"),)

    id = Column(Integer, primary_key=True)
    room_id = Column(Integer, ForeignKey("rooms.id", ondelete="CASCADE"), nullable=False)
    employee_id = Column(Integer, ForeignKey("employees.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(200), nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    room = relationship("Room")
    employee = relationship("Employee")


class Announcement(Base):
    __tablename__ = "announcements"

    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    author_id = Column(Integer, ForeignKey("employees.id", ondelete="SET NULL"))
    pinned = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    author = relationship("Employee")
