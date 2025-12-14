from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class SecurityEventBase(BaseModel):
    asset_id: Optional[int] = None
    severity: str = "info"
    confidence: float = 0.5
    impact: Optional[str] = None
    attack_stage: Optional[str] = None
    category: Optional[str] = None
    risk_score: float = 0.0
    tags: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    description: str
    evidence_refs: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class SecurityEventCreate(SecurityEventBase):
    pass


class SecurityEventRead(SecurityEventBase):
    id: int

    class Config:
        orm_mode = True
