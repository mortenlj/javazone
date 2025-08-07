import textwrap
import zoneinfo
from datetime import datetime, timedelta
from typing import List, Optional
from uuid import UUID

from icalendar import Event, vUri, Alarm, vDuration
from pydantic import ConfigDict
from pydantic.alias_generators import to_camel
from pydantic.main import BaseModel
from pydantic_core import Url

from javazone.sleepingpill import make_url


class UserBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    email: str


class User(UserBase):
    sessions: List["SessionId"]


class SessionId(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        alias_generator=to_camel,
    )
    id: UUID


class Session(SessionId):
    conference_id: UUID
    intended_audience: str
    length: int
    format: str
    language: str
    abstract: str
    title: str
    workshop_prerequisites: Optional[str] = None
    room: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    register_loc: Optional[Url] = None
    start_slot: Optional[datetime] = None
    speakers: list[dict]

    @property
    def description(self) -> str:
        description = textwrap.dedent(
            f"""\
        {self.abstract.replace("\n", "\n        ")}
        
        Speakers: {", ".join(s["name"] for s in self.speakers)}
        Room: {self.room or "TBA"}
        
        More info: {make_url(self.id)}
        """
        )
        return description

    def event(self, *, status=None, transparency=None, priority=None, with_alarm=False, url_for=None) -> Event:
        event = Event()
        event.add("uid", self.id)
        event.add("summary", self.title)
        event.add("class", "PUBLIC")

        if self.start_time:
            event.add("dtstart", self.start_time.replace(tzinfo=zoneinfo.ZoneInfo("Europe/Oslo")))
        if self.end_time:
            event.add("dtend", self.end_time.replace(tzinfo=zoneinfo.ZoneInfo("Europe/Oslo")))
        if self.room:
            event.add("location", self.room)

        uri = vUri(make_url(self.id))
        event.add("url", uri)

        if url_for:
            event.add("description", f"{self.description}\n\n{url_for(self.id)}")
        else:
            event.add("description", self.description)

        if priority is not None:
            event.add("priority", priority)
        if transparency is not None:
            event.add("transp", transparency)
        if status is not None:
            event.add("status", status)

        if with_alarm:
            alarm = Alarm()
            alarm.add("action", "DISPLAY")
            alarm.add("description", "Reminder")
            trigger = vDuration(timedelta(minutes=-15))
            trigger.params["related"] = "START"
            alarm.add("trigger", trigger)

            event.add_component(alarm)

        return event


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
