from typing import List, Optional

from pydantic import BaseModel, Field


class AssetBase(BaseModel):
    ip: str
    hostname: Optional[str] = None
    device_type: Optional[str] = None
    vendor: Optional[str] = None
    model: Optional[str] = None
    serial: Optional[str] = None
    firmware: Optional[str] = None
    protocols: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)


class AssetCreate(AssetBase):
    pass


class AssetRead(AssetBase):
    id: int

    class Config:
        orm_mode = True


class AssetUpdate(BaseModel):
    hostname: Optional[str] = None
    device_type: Optional[str] = None
    vendor: Optional[str] = None
    model: Optional[str] = None
    serial: Optional[str] = None
    firmware: Optional[str] = None
    protocols: Optional[List[str]] = None
    tags: Optional[List[str]] = None
