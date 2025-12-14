import csv
import io
from typing import List

from fastapi import APIRouter, Depends, HTTPException, UploadFile
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


@router.post("/import", response_model=List[AssetRead])
def import_assets(
    *, file: UploadFile, session: Session = Depends(get_session), current_user=Depends(require_role(Role.analyst))
):
    """Bulk-import assets from a CSV file (ip is required)."""

    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV uploads are supported")

    content = file.file.read().decode("utf-8")
    reader = csv.DictReader(io.StringIO(content))
    created: List[Asset] = []
    for row in reader:
        if not row.get("ip"):
            continue
        asset = Asset(
            ip=row.get("ip", "").strip(),
            hostname=row.get("hostname") or None,
            device_type=row.get("device_type") or None,
            vendor=row.get("vendor") or None,
            model=row.get("model") or None,
            serial=row.get("serial") or None,
            firmware=row.get("firmware") or None,
            protocols=[p for p in (row.get("protocols") or "").split(";") if p],
            tags=[t for t in (row.get("tags") or "").split(";") if t],
        )
        session.add(asset)
        created.append(asset)

    session.commit()
    for asset in created:
        session.refresh(asset)
    record_audit(session, actor=current_user.username, action="asset_import", resource="bulk", detail={"count": len(created)})
    return created


@router.get("/export")
def export_assets(*, session: Session = Depends(get_session), current_user=Depends(require_role(Role.viewer))):
    """Export all assets as CSV for offline editing or reuse."""

    output = io.StringIO()
    fieldnames = [
        "id",
        "ip",
        "hostname",
        "device_type",
        "vendor",
        "model",
        "serial",
        "firmware",
        "protocols",
        "tags",
    ]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    for asset in session.exec(select(Asset)):
        writer.writerow(
            {
                "id": asset.id,
                "ip": asset.ip,
                "hostname": asset.hostname or "",
                "device_type": asset.device_type or "",
                "vendor": asset.vendor or "",
                "model": asset.model or "",
                "serial": asset.serial or "",
                "firmware": asset.firmware or "",
                "protocols": ";".join(asset.protocols or []),
                "tags": ";".join(asset.tags or []),
            }
        )

    csv_text = output.getvalue()
    record_audit(
        session,
        actor=current_user.username,
        action="asset_export",
        resource="bulk",
        detail={"count": len(csv_text.splitlines()) - 1},
    )
    return csv_text


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
