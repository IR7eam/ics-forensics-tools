from typing import List, Optional

from pydantic import BaseModel


class PluginSpecRead(BaseModel):
    name: str
    protocol: str
    device_types: List[str]
    default_port: int
    description: str
    read_only: bool = True
    allowed_operations: List[str]
    dangerous_operations: List[str] = []
    enforce_opt_in: bool = True
    notes: Optional[str] = None

    class Config:
        orm_mode = True
