from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class BaselineProfileBase(BaseModel):
    asset_id: Optional[int] = None
    protocol: str
    metrics_baseline: dict = Field(default_factory=dict)
    trained_at: datetime = Field(default_factory=datetime.utcnow)


class BaselineProfileCreate(BaselineProfileBase):
    pass


class BaselineProfileRead(BaselineProfileBase):
    id: int

    class Config:
        orm_mode = True
