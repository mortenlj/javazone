import base64
import json
import logging
import zoneinfo
from datetime import datetime, timedelta

from icalendar import Calendar, Event, vCalAddress, vText, Alarm, vDuration, vUri, vBoolean
from sendgrid import SendGridAPIClient, Attachment
from sendgrid.helpers.mail import Mail
from sqlalchemy import select

from javazone.core.config import settings
from javazone.database import models, get_session
from javazone.database.models import EmailQueue

LOG = logging.getLogger(__name__)


class SendgridException(Exception):
    pass


def _send_enabled():
    return settings.sendgrid.api_key is not None and settings.sendgrid.sender_email is not None


async def process_queue():
    db = get_session()
    try:
        stmt = select(EmailQueue).where(EmailQueue.sent_at.is_(None)).order_by(EmailQueue.scheduled_at).limit(10)
        for eq in db.scalars(stmt):
            LOG.debug("Processing email queue item %r", eq)
            match eq.action:
                case models.Action.INVITE:
                    send_invite(eq)
                case models.Action.CANCEL:
                    send_cancel(eq)
                case models.Action.UPDATE:
                    send_update(eq)
                case _:
                    LOG.error("Unknown action %r", eq.action)
                    continue
            eq.sent_at = datetime.now()
            db.add(eq)
            db.commit()
    finally:
        db.close()


def send_update(eq):
    send_invite(eq)


def send_cancel(eq: EmailQueue):
    session_data = json.loads(eq.data)
    LOG.info("Sending cancel to %s for session %s", eq.user_email, session_data["id"])
    invite = _create_cancel(session_data, eq.user_email)
    title = f"Cancelled: {session_data['title']}"
    _send_message(eq, title, invite)


def send_invite(eq: EmailQueue):
    session_data = json.loads(eq.data)
    LOG.info("Sending invite to %s for session %s", eq.user_email, session_data["id"])
    invite = _create_invite(session_data, eq.user_email)
    _send_message(eq, session_data["title"], invite)


def _send_message(eq: EmailQueue, title: str, invite: Calendar):
    message = Mail(
        from_email=settings.sendgrid.sender_email,
        to_emails=eq.user_email,
        subject=title,
    )

    mime_type = f"text/calendar;method={invite.get("method")}"
    bytes = invite.to_ical()
    message.add_content(bytes.decode("utf-8"), mime_type)

    file_content = base64.b64encode(bytes).decode("utf-8")
    attachment = Attachment(file_content=file_content, file_name="event.ics", file_type=mime_type)
    message.add_attachment(attachment)

    if not _send_enabled():
        LOG.debug("Would have sent email %s", message)
        LOG.debug("iCalendar:\n%s", bytes.decode("utf-8"))
        return
    sg = SendGridAPIClient(settings.sendgrid.api_key.get_secret_value())
    response = sg.send(message)
    if response.status_code < 200 or response.status_code >= 300:
        raise SendgridException(f"Failed to send email: {response.status_code} {response.body}")


def _create_date(iso_date: str) -> datetime:
    dt = datetime.fromisoformat(iso_date)
    return dt.replace(tzinfo=zoneinfo.ZoneInfo("Europe/Oslo"))


def _create_cancel(session: dict, user_email: str) -> Calendar:
    cal = _create_calendar("CANCEL")

    event = Event()
    _add_common_props(event, session)

    event.add("priority", 1)
    event.add("transp", "TRANSPARENT")
    event.add("status", "CANCELLED")

    _add_attendee(event, user_email)

    cal.add_component(event)

    return cal


def _create_invite(session: dict, user_email: str) -> Calendar:
    cal = _create_calendar("REQUEST")

    event = Event()
    _add_common_props(event, session)

    event.add("location", session["room"])
    event.add("priority", 5)
    event.add("transp", "OPAQUE")
    event.add("status", "CONFIRMED")

    _add_attendee(event, user_email)
    _add_url(event, session)

    alarm = Alarm()
    alarm.add("action", "DISPLAY")
    alarm.add("description", "Reminder")
    trigger = vDuration(timedelta(minutes=-15))
    trigger.params["related"] = "START"
    alarm.add("trigger", trigger)

    event.add_component(alarm)
    cal.add_component(event)

    return cal


def _create_calendar(method):
    cal = Calendar()
    cal.add("prodid", "-//JavaZone Calendar Manager//javazone.ibidem.no//")
    cal.add("version", "2.0")
    cal.add("method", method)
    return cal


def _add_common_props(event, session):
    event.add("uid", session["id"])
    event.add("summary", session["title"])
    event.add("dtstart", _create_date(session["startTime"]))
    event.add("dtend", _create_date(session["endTime"]))
    event.add("class", "PUBLIC")
    event.add("description", session["abstract"])


def _add_attendee(event, user_email):
    attendee = vCalAddress(f"MAILTO:{user_email}")
    attendee.params["ROLE"] = vText("REQ-PARTICIPANT")
    attendee.params["PARTSTAT"] = vText("NEEDS-ACTION")
    attendee.params["RSVP"] = vBoolean(False)
    event.add("attendee", attendee, encode=0)


def _add_url(event, session):
    url = vUri(f"https://{settings.year}.javazone.no/program/{session['id']}")
    event.add("url", url)


if __name__ == "__main__":
    session = {
        "id": "1234",
        "title": "Test session title",
        "startTime": "20241010T100000",
        "endTime": "20241010T110000",
        "abstract": "Test session abstract",
        "room": "Test room",
    }
    print("==== INVITE ====")
    cal = _create_invite(session, "mortenjo@ifi.uio.no")
    print(cal.to_ical().decode("utf-8"))
    print("==== CANCEL ====")
    cal = _create_cancel(session, "mortenjo@ifi.uio.no")
    print(cal.to_ical().decode("utf-8"))
