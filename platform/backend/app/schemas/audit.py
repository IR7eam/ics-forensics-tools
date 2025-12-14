from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class AuditLogBase(BaseModel):
    actor: str
    action: str
    resource: str
    status: str = "success"
    detail: dict = Field(default_factory=dict)


class AuditLogCreate(AuditLogBase):
    pass


class AuditLogRead(AuditLogBase):
    id: int
    timestamp: Optional[datetime] = None

    class Config:
        orm_mode = True
