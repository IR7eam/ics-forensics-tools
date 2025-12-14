from typing import List, Optional

from pydantic import BaseModel, Field


class ScanJobBase(BaseModel):
    name: str
    initiated_by: str
    target_range: List[str] = Field(default_factory=list)
    plugins: List[str] = Field(default_factory=list)
    parameters: dict = Field(default_factory=dict)
    status: str = "pending"
    started_at: Optional[str] = None
    finished_at: Optional[str] = None


class ScanJobCreate(ScanJobBase):
    pass


class ScanJobRead(ScanJobBase):
    id: int

    class Config:
        orm_mode = True


class ScanJobUpdate(BaseModel):
    name: Optional[str] = None
    target_range: Optional[List[str]] = None
    plugins: Optional[List[str]] = None
    parameters: Optional[dict] = None
    status: Optional[str] = None
