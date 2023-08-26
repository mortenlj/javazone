from typing import List, Optional
from uuid import UUID

from pydantic.main import BaseModel
from pydantic import ConfigDict


class User(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    email: str
    sessions: List["Session"]


class Session(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    hash: str
    data: str
    users: List["User"] = []


Session.model_rebuild()
User.model_rebuild()
