from datetime import datetime
from typing import Dict, Optional

from pydantic import BaseModel


class EvidenceChainEntry(BaseModel):
    ref: str
    type: str
    timestamp: datetime
    description: str
    attack_stage: Optional[str] = None
    risk_score: Optional[float] = None
    relation: Optional[str] = None
    protocol: Optional[str] = None
    asset_id: Optional[int] = None


class EvidenceChainSummary(BaseModel):
    stage_counts: Dict[str, int]
    max_risk: float
    total_entries: int


class EvidenceChainResponse(BaseModel):
    entries: list[EvidenceChainEntry]
    summary: EvidenceChainSummary
