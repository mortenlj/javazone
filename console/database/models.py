import datetime
import uuid
from typing import Set

from sqlalchemy import Column, DateTime, ForeignKey, Table, Text, inspect
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_mixin, declared_attr, relationship

from . import Base


@declarative_mixin
class Common:
    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower() + "s"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime, default=datetime.datetime.now)

    @declared_attr
    def created_by_id(cls):
        return Column(UUID, ForeignKey("users.id"))

    @declared_attr
    def created_by(cls):
        return relationship("User", primaryjoin=lambda: User.id == cls.created_by_id)

    updated_at = Column(DateTime, onupdate=datetime.datetime.now)

    @declared_attr
    def updated_by_id(cls):
        return Column(UUID, ForeignKey("users.id"))

    @declared_attr
    def updated_by(cls):
        return relationship("User", primaryjoin=lambda: User.id == cls.updated_by_id)

    deleted_at = Column(DateTime)

    @declared_attr
    def deleted_by_id(cls):
        return Column(UUID, ForeignKey("users.id"))

    @declared_attr
    def deleted_by(cls):
        return relationship("User", primaryjoin=lambda: User.id == cls.deleted_by_id)

    @classmethod
    def fields(cls) -> Set[str]:
        mapper = inspect(cls)
        return {c.name for c in mapper.columns}


user_team = Table(
    "association",
    Base.metadata,
    Column("user_id", ForeignKey("users.id"), primary_key=True),
    Column("team_id", ForeignKey("teams.id"), primary_key=True),
)


class Team(Common, Base):
    slug = Column(Text, unique=True, nullable=False)
    name = Column(Text, unique=True, nullable=False)
    purpose = Column(Text)
    users = relationship("User", secondary=user_team, back_populates="teams")


class User(Common, Base):
    email = Column(Text, unique=True)
    name = Column(Text, nullable=False)
    teams = relationship("Team", secondary=user_team, back_populates="users")


class ApiKey(Common, Base):
    api_key = Column(Text, unique=True, nullable=False)
    user_id = Column(UUID, ForeignKey("users.id"), unique=True, nullable=False)
    user = relationship("User", uselist=False, foreign_keys="ApiKey.user_id")
