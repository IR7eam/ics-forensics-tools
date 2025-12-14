from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class RulePackBase(BaseModel):
    name: str
    description: Optional[str] = None
    enabled: bool = True
    tags: List[str] = Field(default_factory=list)
    rules: List[dict]


class RulePackCreate(RulePackBase):
    pass


class RulePackUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    enabled: Optional[bool] = None
    tags: Optional[List[str]] = None
    rules: Optional[List[dict]] = None


class RulePackRead(RulePackBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
