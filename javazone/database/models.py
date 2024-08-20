import enum
import uuid
from datetime import datetime

from sqlalchemy import Column, ForeignKey, Table, Text, Uuid, String, Enum, DateTime
from sqlalchemy.orm import relationship

from . import Base

user_session = Table(
    "user_session",
    Base.metadata,
    Column("user_email", ForeignKey("users.email"), primary_key=True),
    Column("session_id", ForeignKey("sessions.id"), primary_key=True),
)


class Session(Base):
    __tablename__ = "sessions"

    id = Column(Uuid(as_uuid=True), unique=True, primary_key=True, nullable=False)
    hash = Column(String(64), nullable=False)
    data = Column(Text, nullable=False)
    users = relationship("User", secondary=user_session, back_populates="sessions")


class User(Base):
    __tablename__ = "users"

    email = Column(String(256), unique=True, primary_key=True, nullable=False)
    sessions = relationship("Session", secondary=user_session, back_populates="users")


class Action(enum.StrEnum):
    INVITE = enum.auto()
    UPDATE = enum.auto()
    CANCEL = enum.auto()


class EmailQueue(Base):
    __tablename__ = "email_queue"

    id = Column(Uuid(as_uuid=True), unique=True, primary_key=True, nullable=False, default=uuid.uuid4)
    user_email = Column(String(256), nullable=False)
    data = Column(Text, nullable=False)
    action = Column(Enum(Action), nullable=False)
    scheduled_at = Column(DateTime, nullable=False, default=datetime.now)
    sent_at = Column(DateTime, nullable=True)
