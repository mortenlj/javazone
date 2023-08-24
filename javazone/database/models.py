import uuid
from sqlalchemy import Column, ForeignKey, Table, Text, Uuid
from sqlalchemy.orm import relationship, declarative_mixin, declared_attr
from typing import Set

from . import Base


@declarative_mixin
class Common:
    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower() + "s"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)

    @classmethod
    def fields(cls) -> Set[str]:
        mapper = inspect(cls)
        return {c.name for c in mapper.columns}


user_session = Table(
    "association",
    Base.metadata,
    Column("user_id", ForeignKey("users.id"), primary_key=True),
    Column("session_id", ForeignKey("sessions.id"), primary_key=True),
)


class Session(Common, Base):
    title = Column(Text, unique=False, nullable=False)
    hash = Column(Text, unique=False)
    users = relationship("User", secondary=user_session, back_populates="sessions")


class User(Common, Base):
    email = Column(Text, unique=True)
    sessions = relationship("Session", secondary=user_session, back_populates="users")
