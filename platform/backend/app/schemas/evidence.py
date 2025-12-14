from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class RawEvidenceBase(BaseModel):
    observation_id: Optional[int] = None
    hash: str
    storage_path: str
    context: dict = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class RawEvidenceCreate(RawEvidenceBase):
    pass


class RawEvidenceRead(RawEvidenceBase):
    id: int

    class Config:
        orm_mode = True
