import textwrap
import zoneinfo
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Annotated
from uuid import UUID

from icalendar import Event, vUri, Alarm, vDuration
from pydantic import BaseModel, ConfigDict, HttpUrl, AnyUrl, BeforeValidator
from pydantic.alias_generators import to_camel

from javazone.core.config import settings

DEFAULT_URL_PATTERN = "https://{year}.javazone.no/program/{session_id}"
JAVAZONE_URL_PATTERNS = {
    2025: "https://2025.javazone.no/en/program/{session_id}",
}


def empty_str_to_none(v: Any) -> Any:
    if isinstance(v, str) and v == "":
        return None
    return v


EmptyInt = Annotated[Optional[int], BeforeValidator(empty_str_to_none)]


class UserBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class AuthenticatedUser(UserBase):
    email: str
    name: str = ""
    picture_url: Optional[HttpUrl] = None

    def __eq__(self, other):
        for field in AuthenticatedUser.model_fields.keys():
            if getattr(self, field) != getattr(other, field, None):
                return False
        return True

    @property
    def picture(self) -> str:
        if self.picture_url:
            return str(self.picture_url)
        return "https://icons.getbootstrap.com/assets/icons/question-circle.svg"


class User(AuthenticatedUser):
    sessions: List["SessionId"]


class SessionId(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        alias_generator=to_camel,
    )
    id: UUID

    def make_url(self):
        pattern = JAVAZONE_URL_PATTERNS.get(settings.year, DEFAULT_URL_PATTERN)
        return pattern.format(year=settings.year, session_id=self.id)


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
    register_loc: Optional[AnyUrl] = None
    start_slot: Optional[datetime] = None
    video: EmptyInt = None
    speakers: list[dict]

    @classmethod
    def from_db_session(cls, db_session):
        session = cls.model_validate_json(db_session.data)
        return session

    @property
    def calendar_description(self) -> str:
        description = textwrap.dedent(
            f"""\
        {self.abstract.replace("\n", "\n        ")}
        
        Speakers: {", ".join(s["name"] for s in self.speakers)}
        Room: {self.room or "TBA"}
        Video: {self.video_url() or 'Not yet available'}
        
        More info: {self.make_url()}
        """
        )
        return description

    def video_url(self) -> Optional[str]:
        if self.video:
            return f"https://vimeo.com/{self.video}"
        return None

    def language_name(self):
        return {
            "en": "English",
            "no": "Norwegian",
        }.get(self.language, self.language)

    def start(self) -> str:
        if self.start_time:
            return self.start_time.strftime("%H:%M")
        return "TBA"

    def duration(self) -> str:
        if self.start_time and self.end_time:
            delta = self.end_time - self.start_time
            hours, remainder = divmod(delta.total_seconds(), 60 * 60)
            minutes, _seconds = divmod(remainder, 60)
            parts = []
            if hours > 0:
                parts.append(f"{int(hours)} hours")
            if minutes > 0:
                if hours > 0:
                    parts.append("and")
                parts.append(f"{int(minutes)} min")
            return " ".join(parts)
        return ""

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

        uri = vUri(self.make_url())
        event.add("url", uri)

        if url_for:
            event.add("description", f"{self.calendar_description}\n\n{url_for(self.id)}")
        else:
            event.add("description", self.calendar_description)

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
    users: List["AuthenticatedUser"] = []

    @classmethod
    def from_db_session(cls, db_session):
        session = cls.model_validate_json(db_session.data)
        session.users = [AuthenticatedUser.model_validate(u) for u in db_session.users]
        return session


class SessionSlot(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    start_time: datetime
    _sessions: List[Session] = []

    def start(self) -> str:
        if self.start_time:
            return self.start_time.strftime("%H:%M")
        return "TBA"

    @property
    def sessions(self) -> List[Session]:
        return list(sorted(self._sessions, key=lambda session: session.room))

    def add_session(self, session: Session):
        if session.start_time != self.start_time:
            raise ValueError("Session start time does not match block start time")
        self._sessions.append(session)


class SessionsDay(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    _session_slots: Dict[datetime, SessionSlot] = {}

    @property
    def session_slots(self) -> List[SessionSlot]:
        return list(sorted(self._session_slots.values(), key=lambda block: block.start_time))

    def add_session(self, session: Session):
        slot = self._session_slots.setdefault(session.start_slot, SessionSlot(start_time=session.start_slot))
        slot.add_session(session)


class SessionsPage(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    title: str
    description: str
    days: List[SessionsDay] = []


SessionWithUsers.model_rebuild()
Session.model_rebuild()
User.model_rebuild()
UserBase.model_rebuild()
