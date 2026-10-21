from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user, require_roles
from ..models import Announcement, Employee
from ..schemas import AnnouncementCreate, AnnouncementOut, AnnouncementUpdate

router = APIRouter(prefix="/api/announcements", tags=["Thông báo"])


def to_out(a: Announcement) -> AnnouncementOut:
    return AnnouncementOut(
        id=a.id,
        title=a.title,
        content=a.content,
        pinned=a.pinned,
        author_id=a.author_id,
        author_name=a.author.full_name if a.author else None,
        created_at=a.created_at,
    )


@router.get("", response_model=list[AnnouncementOut], dependencies=[Depends(get_current_user)])
def list_announcements(db: Session = Depends(get_db)):
    rows = db.query(Announcement).order_by(Announcement.pinned.desc(), Announcement.created_at.desc()).all()
    return [to_out(a) for a in rows]


@router.post("", response_model=AnnouncementOut, status_code=201)
def create_announcement(
    data: AnnouncementCreate,
    db: Session = Depends(get_db),
    user: Employee = Depends(require_roles("admin", "manager")),
):
    item = Announcement(**data.model_dump(), author_id=user.id)
    db.add(item)
    db.commit()
    db.refresh(item)
    return to_out(item)


@router.put("/{item_id}", response_model=AnnouncementOut)
def update_announcement(
    item_id: int,
    data: AnnouncementUpdate,
    db: Session = Depends(get_db),
    user: Employee = Depends(require_roles("admin", "manager")),
):
    item = db.get(Announcement, item_id)
    if not item:
        raise HTTPException(404, "Không tìm thấy thông báo")
    if user.role != "admin" and item.author_id != user.id:
        raise HTTPException(403, "Chỉ tác giả hoặc admin mới được sửa")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(item, key, value)
    db.commit()
    db.refresh(item)
    return to_out(item)


@router.delete("/{item_id}")
def delete_announcement(
    item_id: int,
    db: Session = Depends(get_db),
    user: Employee = Depends(require_roles("admin", "manager")),
):
    item = db.get(Announcement, item_id)
    if not item:
        raise HTTPException(404, "Không tìm thấy thông báo")
    if user.role != "admin" and item.author_id != user.id:
        raise HTTPException(403, "Chỉ tác giả hoặc admin mới được xóa")
    db.delete(item)
    db.commit()
    return {"message": "Đã xóa thông báo"}
