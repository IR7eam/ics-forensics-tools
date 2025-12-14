from typing import List, Optional

from pydantic import BaseModel, Field


class ScanJobBase(BaseModel):
    name: str
    initiated_by: str
    target_range: List[str] = Field(default_factory=list)
    plugins: List[str] = Field(default_factory=list)
    parameters: dict = Field(default_factory=dict)
    connect_timeout_s: float = 3.0
    read_timeout_s: float = 5.0
    rate_limit_rps: float = 1.0
    max_retries: int = 1
    retry_backoff_s: float = 0.5
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
    connect_timeout_s: Optional[float] = None
    read_timeout_s: Optional[float] = None
    rate_limit_rps: Optional[float] = None
    max_retries: Optional[int] = None
    retry_backoff_s: Optional[float] = None
    status: Optional[str] = None
