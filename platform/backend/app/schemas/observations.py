from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class ObservationBase(BaseModel):
    asset_id: Optional[int] = None
    protocol: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    parsed_data: dict = Field(default_factory=dict)
    metrics: dict = Field(default_factory=dict)
    raw_refs: List[str] = Field(default_factory=list)


class ObservationCreate(ObservationBase):
    pass


class ObservationRead(ObservationBase):
    id: int

    class Config:
        orm_mode = True
