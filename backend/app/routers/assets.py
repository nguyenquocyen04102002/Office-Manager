from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user, require_roles
from ..models import Asset, Employee
from ..schemas import AssetCreate, AssetOut, AssetUpdate

router = APIRouter(prefix="/api/assets", tags=["Tài sản"])
manage = require_roles("admin", "manager")


def to_out(a: Asset) -> AssetOut:
    return AssetOut(
        id=a.id,
        code=a.code,
        name=a.name,
        category=a.category,
        status=a.status,
        assigned_to_id=a.assigned_to_id,
        purchase_date=a.purchase_date,
        note=a.note,
        assigned_to_name=a.assigned_to.full_name if a.assigned_to else None,
    )


def _normalize(values: dict):
    """Giữ trạng thái và người sử dụng nhất quán."""
    if values.get("assigned_to_id") and "status" not in values:
        values["status"] = "in_use"
    if values.get("status") in ("available", "retired", "maintenance") and "assigned_to_id" not in values:
        values["assigned_to_id"] = None
    return values


@router.get("", response_model=list[AssetOut], dependencies=[Depends(get_current_user)])
def list_assets(
    q: Optional[str] = None,
    status: Optional[str] = None,
    category: Optional[str] = None,
    db: Session = Depends(get_db),
):
    query = db.query(Asset)
    if q:
        like = f"%{q.strip()}%"
        query = query.filter(or_(Asset.name.ilike(like), Asset.code.ilike(like)))
    if status:
        query = query.filter(Asset.status == status)
    if category:
        query = query.filter(Asset.category == category)
    return [to_out(a) for a in query.order_by(Asset.code).all()]


@router.post("", response_model=AssetOut, status_code=201, dependencies=[Depends(manage)])
def create_asset(data: AssetCreate, db: Session = Depends(get_db)):
    if db.query(Asset).filter(Asset.code == data.code).first():
        raise HTTPException(400, "Mã tài sản đã tồn tại")
    values = _normalize(data.model_dump(exclude_unset=True))
    if values.get("assigned_to_id") and not db.get(Employee, values["assigned_to_id"]):
        raise HTTPException(400, "Người sử dụng không tồn tại")
    asset = Asset(**{**data.model_dump(), **values})
    db.add(asset)
    db.commit()
    db.refresh(asset)
    return to_out(asset)


@router.put("/{asset_id}", response_model=AssetOut, dependencies=[Depends(manage)])
def update_asset(asset_id: int, data: AssetUpdate, db: Session = Depends(get_db)):
    asset = db.get(Asset, asset_id)
    if not asset:
        raise HTTPException(404, "Không tìm thấy tài sản")
    values = _normalize(data.model_dump(exclude_unset=True))
    if "code" in values and db.query(Asset).filter(Asset.code == values["code"], Asset.id != asset_id).first():
        raise HTTPException(400, "Mã tài sản đã tồn tại")
    if values.get("assigned_to_id") and not db.get(Employee, values["assigned_to_id"]):
        raise HTTPException(400, "Người sử dụng không tồn tại")
    for key, value in values.items():
        setattr(asset, key, value)
    db.commit()
    db.refresh(asset)
    return to_out(asset)


@router.delete("/{asset_id}", dependencies=[Depends(require_roles("admin"))])
def delete_asset(asset_id: int, db: Session = Depends(get_db)):
    asset = db.get(Asset, asset_id)
    if not asset:
        raise HTTPException(404, "Không tìm thấy tài sản")
    db.delete(asset)
    db.commit()
    return {"message": "Đã xóa tài sản"}
