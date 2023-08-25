from typing import List, Optional
from uuid import UUID

from pydantic.main import BaseModel


class User(BaseModel):
    class Config:
        orm_mode = True

    email: str
    sessions: List["Session"]


class Session(BaseModel):
    class Config:
        orm_mode = True

    id: UUID
    title: str
    hash: str
    users: List["User"] = []


Session.update_forward_refs()
User.update_forward_refs()
