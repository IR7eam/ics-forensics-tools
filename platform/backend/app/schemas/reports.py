from typing import Dict, Optional

from pydantic import BaseModel, Field


class ReportBase(BaseModel):
    scope: Dict = Field(default_factory=dict)
    parameters: Dict = Field(default_factory=dict)
    format: str = "html"
    file_path: Optional[str] = None


class ReportCreate(ReportBase):
    title: str = "ICS Forensics Report"


class ReportRead(ReportBase):
    id: int

    class Config:
        orm_mode = True
