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


class BaselineTrainRequest(BaseModel):
    asset_id: int
    protocol: str
    observations_limit: int = 200


class BaselineEvaluateRequest(BaseModel):
    asset_id: int
    protocol: str
    metrics: dict = Field(default_factory=dict)
    threshold: float = 3.0
    create_event: bool = True


class BaselineEvaluateResult(BaseModel):
    comparison: dict
    deviations: list[str]
    event_id: Optional[int] = None
