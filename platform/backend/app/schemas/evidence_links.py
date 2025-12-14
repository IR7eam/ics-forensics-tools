from pydantic import BaseModel


class EvidenceLinkBase(BaseModel):
    from_ref: str
    to_ref: str
    relation: str


class EvidenceLinkCreate(EvidenceLinkBase):
    pass


class EvidenceLinkRead(EvidenceLinkBase):
    id: int

    class Config:
        orm_mode = True
