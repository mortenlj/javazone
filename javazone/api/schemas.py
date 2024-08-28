from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import ConfigDict
from pydantic.alias_generators import to_camel
from pydantic.main import BaseModel
from pydantic_core import Url


class UserBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    email: str


class User(UserBase):
    sessions: List["Session"]


class Session(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        alias_generator=to_camel,
    )

    id: UUID
    conference_id: UUID
    intended_audience: str
    length: int
    format: str
    language: str
    abstract: str
    title: str
    workshop_prerequisites: Optional[str] = None
    room: str
    start_time: datetime
    end_time: datetime
    register_loc: Optional[Url] = None
    start_slot: datetime
    speakers: list[dict]


class SessionWithUsers(Session):
    users: List["UserBase"] = []

    @classmethod
    def from_db_session(cls, db_session):
        session = cls.model_validate_json(db_session.data)
        session.users = [UserBase.model_validate(u) for u in db_session.users]
        return session


SessionWithUsers.model_rebuild()
Session.model_rebuild()
User.model_rebuild()
UserBase.model_rebuild()
