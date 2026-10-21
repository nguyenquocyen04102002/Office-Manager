from datetime import date, datetime, time, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user, require_roles
from ..models import Booking, Employee, Room
from ..schemas import BookingCreate, BookingOut, RoomCreate, RoomOut, RoomUpdate

router = APIRouter(prefix="/api", tags=["Phòng họp"])


def booking_out(b: Booking) -> BookingOut:
    return BookingOut(
        id=b.id,
        room_id=b.room_id,
        room_name=b.room.name if b.room else None,
        employee_id=b.employee_id,
        employee_name=b.employee.full_name if b.employee else None,
        title=b.title,
        start_time=b.start_time,
        end_time=b.end_time,
    )


# ---------------- Phòng họp ----------------
@router.get("/rooms", response_model=list[RoomOut], dependencies=[Depends(get_current_user)])
def list_rooms(db: Session = Depends(get_db)):
    return db.query(Room).order_by(Room.name).all()


@router.post("/rooms", response_model=RoomOut, status_code=201, dependencies=[Depends(require_roles("admin"))])
def create_room(data: RoomCreate, db: Session = Depends(get_db)):
    if db.query(Room).filter(Room.name == data.name).first():
        raise HTTPException(400, "Tên phòng đã tồn tại")
    room = Room(**data.model_dump())
    db.add(room)
    db.commit()
    db.refresh(room)
    return room


@router.put("/rooms/{room_id}", response_model=RoomOut, dependencies=[Depends(require_roles("admin"))])
def update_room(room_id: int, data: RoomUpdate, db: Session = Depends(get_db)):
    room = db.get(Room, room_id)
    if not room:
        raise HTTPException(404, "Không tìm thấy phòng họp")
    values = data.model_dump(exclude_unset=True)
    if "name" in values and db.query(Room).filter(Room.name == values["name"], Room.id != room_id).first():
        raise HTTPException(400, "Tên phòng đã tồn tại")
    for key, value in values.items():
        setattr(room, key, value)
    db.commit()
    db.refresh(room)
    return room


@router.delete("/rooms/{room_id}", dependencies=[Depends(require_roles("admin"))])
def delete_room(room_id: int, db: Session = Depends(get_db)):
    room = db.get(Room, room_id)
    if not room:
        raise HTTPException(404, "Không tìm thấy phòng họp")
    db.query(Booking).filter(Booking.room_id == room_id).delete()
    db.delete(room)
    db.commit()
    return {"message": "Đã xóa phòng họp"}


# ---------------- Đặt phòng ----------------
@router.get("/bookings", response_model=list[BookingOut], dependencies=[Depends(get_current_user)])
def list_bookings(
    day: Optional[date] = None,
    room_id: Optional[int] = None,
    upcoming: bool = False,
    db: Session = Depends(get_db),
):
    query = db.query(Booking)
    if day:
        query = query.filter(
            Booking.start_time >= datetime.combine(day, time.min),
            Booking.start_time < datetime.combine(day + timedelta(days=1), time.min),
        )
    if upcoming:
        query = query.filter(Booking.end_time >= datetime.now())
    if room_id:
        query = query.filter(Booking.room_id == room_id)
    return [booking_out(b) for b in query.order_by(Booking.start_time).all()]


@router.post("/bookings", response_model=BookingOut, status_code=201, summary="Đặt phòng họp")
def create_booking(data: BookingCreate, db: Session = Depends(get_db), user: Employee = Depends(get_current_user)):
    if not db.get(Room, data.room_id):
        raise HTTPException(400, "Phòng họp không tồn tại")
    if data.end_time <= data.start_time:
        raise HTTPException(400, "Giờ kết thúc phải sau giờ bắt đầu")
    conflict = (
        db.query(Booking)
        .filter(
            Booking.room_id == data.room_id,
            Booking.start_time < data.end_time,
            Booking.end_time > data.start_time,
        )
        .first()
    )
    if conflict:
        raise HTTPException(
            409,
            f"Phòng đã được đặt từ {conflict.start_time:%H:%M} đến {conflict.end_time:%H:%M} ({conflict.start_time:%d/%m/%Y})",
        )
    booking = Booking(**data.model_dump(), employee_id=user.id)
    db.add(booking)
    db.commit()
    db.refresh(booking)
    return booking_out(booking)


@router.delete("/bookings/{booking_id}", summary="Hủy lịch đặt phòng")
def cancel_booking(booking_id: int, db: Session = Depends(get_db), user: Employee = Depends(get_current_user)):
    booking = db.get(Booking, booking_id)
    if not booking:
        raise HTTPException(404, "Không tìm thấy lịch đặt phòng")
    if booking.employee_id != user.id and user.role != "admin":
        raise HTTPException(403, "Bạn chỉ có thể hủy lịch do chính mình đặt")
    db.delete(booking)
    db.commit()
    return {"message": "Đã hủy lịch đặt phòng"}
