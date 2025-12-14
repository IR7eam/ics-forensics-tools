from datetime import datetime
from typing import List, Optional

from sqlalchemy import Column, JSON as SAJSON
from sqlmodel import Field, SQLModel


class Asset(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    ip: str
    hostname: Optional[str] = None
    device_type: Optional[str] = None
    vendor: Optional[str] = None
    model: Optional[str] = None
    serial: Optional[str] = None
    firmware: Optional[str] = None
    protocols: List[str] = Field(default_factory=list, sa_column=Column(SAJSON))
    tags: List[str] = Field(default_factory=list, sa_column=Column(SAJSON))
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)


class ScanJob(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    initiated_by: str
    target_range: List[str] = Field(default_factory=list, sa_column=Column(SAJSON))
    plugins: List[str] = Field(default_factory=list, sa_column=Column(SAJSON))
    parameters: dict = Field(default_factory=dict, sa_column=Column(SAJSON))
    connect_timeout_s: float = 3.0
    read_timeout_s: float = 5.0
    rate_limit_rps: float = 1.0
    max_retries: int = 1
    retry_backoff_s: float = 0.5
    status: str = "pending"
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Observation(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    asset_id: Optional[int] = Field(default=None, foreign_key="asset.id")
    protocol: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    parsed_data: dict = Field(default_factory=dict, sa_column=Column(SAJSON))
    metrics: dict = Field(default_factory=dict, sa_column=Column(SAJSON))
    raw_refs: List[str] = Field(default_factory=list, sa_column=Column(SAJSON))


class RawEvidence(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    observation_id: Optional[int] = Field(default=None, foreign_key="observation.id")
    hash: str
    storage_path: str
    context: dict = Field(default_factory=dict, sa_column=Column(SAJSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)


class SecurityEvent(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    asset_id: Optional[int] = Field(default=None, foreign_key="asset.id")
    severity: str = "info"
    confidence: float = 0.5
    impact: Optional[str] = None
    attack_stage: Optional[str] = None
    category: Optional[str] = None
    risk_score: float = 0.0
    tags: List[str] = Field(default_factory=list, sa_column=Column(SAJSON))
    recommendations: List[str] = Field(default_factory=list, sa_column=Column(SAJSON))
    description: str
    evidence_refs: List[str] = Field(default_factory=list, sa_column=Column(SAJSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)


class EvidenceLink(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    from_ref: str
    to_ref: str
    relation: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Report(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    scope: dict = Field(default_factory=dict, sa_column=Column(SAJSON))
    parameters: dict = Field(default_factory=dict, sa_column=Column(SAJSON))
    format: str = "html"
    file_path: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class BaselineProfile(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    asset_id: Optional[int] = Field(default=None, foreign_key="asset.id")
    protocol: str
    metrics_baseline: dict = Field(default_factory=dict, sa_column=Column(SAJSON))
    trained_at: datetime = Field(default_factory=datetime.utcnow)


class AuditLog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    actor: str
    action: str
    resource: str
    status: str = "success"
    detail: dict = Field(default_factory=dict, sa_column=Column(SAJSON))
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class RulePack(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    description: Optional[str] = None
    enabled: bool = True
    tags: List[str] = Field(default_factory=list, sa_column=Column(SAJSON))
    rules: List[dict] = Field(default_factory=list, sa_column=Column(SAJSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
