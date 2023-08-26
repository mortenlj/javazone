from sqlalchemy import Column, ForeignKey, Table, Text, Uuid, String
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
    hash = Column(Text, nullable=False)
    json = Column(Text, nullable=False)
    users = relationship("User", secondary=user_session, back_populates="sessions")


class User(Base):
    __tablename__ = "users"

    email = Column(String(256), unique=True, primary_key=True, nullable=False)
    sessions = relationship("Session", secondary=user_session, back_populates="users")
