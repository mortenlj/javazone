from pydantic.main import BaseModel
from typing import List, Optional
from uuid import UUID


class Common(BaseModel):
    class Config:
        orm_mode = True

    id: Optional[UUID] = None


class User(Common):
    email: str
    sessions: List["Session"]


class Session(Common):
    title: str
    hash: Optional[str] = None
    users: List["User"] = []


Common.update_forward_refs()
Session.update_forward_refs()
User.update_forward_refs()
