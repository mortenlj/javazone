from typing import List
from uuid import UUID

from pydantic import ConfigDict
from pydantic.main import BaseModel


class UserBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    email: str


class User(UserBase):
    sessions: List["SessionBase"]


class SessionBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    hash: str
    data: str


class Session(SessionBase):
    users: List["UserBase"] = []


Session.model_rebuild()
SessionBase.model_rebuild()
User.model_rebuild()
UserBase.model_rebuild()
