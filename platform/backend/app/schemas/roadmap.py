from typing import List, Literal

from pydantic import BaseModel


class RoadmapItem(BaseModel):
    title: str
    detail: str
    status: Literal["done", "in_progress", "planned"]
    category: str


class RoadmapSummary(BaseModel):
    iterations_remaining: int
    focus_areas: List[str]
    delivered: List[RoadmapItem]
    in_progress: List[RoadmapItem]
    remaining: List[RoadmapItem]
    blockers: List[str]
