from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.core.security import Role, require_role
from app.db.session import get_session
from app.models.core import Asset
from app.schemas.assets import AssetCreate, AssetRead, AssetUpdate
from app.services.audit import record_audit

router = APIRouter(prefix="/assets", tags=["assets"])


@router.get("/", response_model=List[AssetRead])
def list_assets(*, session: Session = Depends(get_session), current_user=Depends(require_role(Role.viewer))):
    return session.exec(select(Asset)).all()


@router.post("/", response_model=AssetRead)
def create_asset(asset: AssetCreate, session: Session = Depends(get_session), current_user=Depends(require_role(Role.analyst))):
    db_asset = Asset.from_orm(asset)
    session.add(db_asset)
    session.commit()
    session.refresh(db_asset)
    record_audit(
        session,
        actor=current_user.username,
        action="asset_create",
        resource=str(db_asset.id),
        detail={"ip": db_asset.ip, "hostname": db_asset.hostname},
    )
    return db_asset


@router.get("/{asset_id}", response_model=AssetRead)
def get_asset(asset_id: int, session: Session = Depends(get_session), current_user=Depends(require_role(Role.viewer))):
    asset = session.get(Asset, asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return asset


@router.put("/{asset_id}", response_model=AssetRead)
def update_asset(asset_id: int, asset: AssetUpdate, session: Session = Depends(get_session), current_user=Depends(require_role(Role.analyst))):
    db_asset = session.get(Asset, asset_id)
    if not db_asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    update_data = asset.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_asset, key, value)
    session.add(db_asset)
    session.commit()
    session.refresh(db_asset)
    record_audit(
        session,
        actor=current_user.username,
        action="asset_update",
        resource=str(db_asset.id),
        detail=update_data,
    )
    return db_asset


@router.delete("/{asset_id}")
def delete_asset(asset_id: int, session: Session = Depends(get_session), current_user=Depends(require_role(Role.admin))):
    asset = session.get(Asset, asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    session.delete(asset)
    session.commit()
    record_audit(
        session,
        actor=current_user.username,
        action="asset_delete",
        resource=str(asset_id),
    )
    return {"ok": True}
