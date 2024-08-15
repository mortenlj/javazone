import base64
import zoneinfo
from datetime import datetime
import json
import logging

from icalendar import Calendar, Event
from sendgrid import SendGridAPIClient, Attachment
from sendgrid.helpers.mail import Mail

from javazone.api import schemas
from javazone.core.config import settings
from javazone.database import models

LOG = logging.getLogger(__name__)


def _send_enabled():
    return settings.sendgrid.api_key is not None and settings.sendgrid.sender_email is not None


def send_invite(session: models.Session, user: schemas.User):
    if not _send_enabled():
        return
    LOG.info("Sending invite to %s for session %s", user.email, session.id)
    session_data = json.loads(session.data)
    message = Mail(
        from_email=settings.sendgrid.sender_email,
        to_emails=user.email,
        subject=session_data["title"],
        plain_text_content=session_data["abstract"],
    )
    invite = _create_invite(session_data, user.email)
    message.add_attachment(invite)
    try:
        sg = SendGridAPIClient(settings.sendgrid.api_key.get_secret_value())
        response = sg.send(message)
        LOG.debug(response.status_code)
        LOG.debug(response.body)
        LOG.debug(response.headers)
    except Exception as e:
        LOG.error(e)


def _create_date(iso_date: str) -> datetime:
    dt = datetime.fromisoformat(iso_date)
    return dt.replace(tzinfo=zoneinfo.ZoneInfo("Europe/Oslo"))


def _create_invite(session: dict, user_email: str) -> Attachment:
    cal = Calendar()
    cal.add("prodid", "-//JavaZone Calendar Manager//javazone.ibidem.no//")
    cal.add("version", "2.0")
    cal.add("method", "REQUEST")

    event = Event()
    event.add("summary", session["title"])
    event.add("dtstart", _create_date(session["startTime"]))
    event.add("dtend", _create_date(session["endTime"]))

    cal.add_component(event)

    contents = base64.b64encode(cal.to_ical()).decode("utf-8")

    return Attachment(file_content=contents, file_name="event.ics", file_type="text/calendar")
