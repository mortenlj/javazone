from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic.main import BaseModel


class Common(BaseModel):
    class Config:
        orm_mode = True

    id: Optional[UUID] = None
    created_at: Optional[datetime] = None
    created_by: Optional["User"] = None
    updated_at: Optional[datetime] = None
    updated_by: Optional["User"] = None
    deleted_at: Optional[datetime] = None
    deleted_by: Optional["User"] = None


class User(Common):
    email: str
    name: str
    teams: List["Team"]


class Team(Common):
    slug: str
    name: str
    purpose: Optional[str] = None
    users: List["User"] = []


Common.update_forward_refs()
Team.update_forward_refs()
User.update_forward_refs()
