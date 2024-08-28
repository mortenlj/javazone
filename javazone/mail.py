import base64
import logging
import textwrap
import zoneinfo
from datetime import datetime, timedelta

from icalendar import Calendar, Event, vCalAddress, vText, Alarm, vDuration, vUri, vBoolean
from sendgrid import SendGridAPIClient, Attachment
from sendgrid.helpers.mail import Mail
from sqlalchemy import select

from javazone.api import schemas
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
            session = schemas.Session.model_validate_json(eq.data)
            match eq.action:
                case models.Action.INVITE:
                    send_invite(eq, session)
                case models.Action.CANCEL:
                    send_cancel(eq, session)
                case models.Action.UPDATE:
                    send_update(eq, session)
                case _:
                    LOG.error("Unknown action %r", eq.action)
                    continue
            eq.sent_at = datetime.now()
            db.add(eq)
            db.commit()
    finally:
        db.close()


def send_update(eq, session):
    send_invite(eq, session)


def send_cancel(eq: EmailQueue, session: schemas.Session):
    LOG.info("Sending cancel to %s for session %s", eq.user_email, session.id)
    invite = _create_cancel(session, eq.user_email)
    title = f"Cancelled: {session.title}"
    _send_message(eq, title, invite)


def send_invite(eq: EmailQueue, session: schemas.Session):
    LOG.info("Sending invite to %s for session %s", eq.user_email, session.id)
    invite = _create_invite(session, eq.user_email)
    _send_message(eq, session.title, invite)


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
        LOG.info("Send is disabled! Would have sent email %s", message)
        LOG.debug("iCalendar:\n%s", bytes.decode("utf-8"))
        return
    sg = SendGridAPIClient(settings.sendgrid.api_key.get_secret_value())
    response = sg.send(message)
    if response.status_code < 200 or response.status_code >= 300:
        raise SendgridException(f"Failed to send email: {response.status_code} {response.body}")


def _replace_tz(dt: datetime) -> datetime:
    return dt.replace(tzinfo=zoneinfo.ZoneInfo("Europe/Oslo"))


def _create_cancel(session: schemas.Session, user_email: str) -> Calendar:
    cal = _create_calendar("CANCEL")

    event = Event()
    _add_common_props(event, session)

    event.add("priority", 1)
    event.add("transp", "TRANSPARENT")
    event.add("status", "CANCELLED")

    _add_attendee(event, user_email)

    cal.add_component(event)

    return cal


def _create_invite(session: schemas.Session, user_email: str) -> Calendar:
    cal = _create_calendar("REQUEST")

    event = Event()
    _add_common_props(event, session)

    event.add("location", session.room)
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


def _make_description(session: schemas.Session):
    description = textwrap.dedent(
        f"""\
    {session.abstract}
    
    Speakers: {", ".join(s["name"] for s in session.speakers)}
    Room: {session.room}
    
    More info: {_make_url(session)}
    """
    )
    return description


def _create_calendar(method):
    cal = Calendar()
    cal.add("prodid", "-//JavaZone Calendar Manager//javazone.ibidem.no//")
    cal.add("version", "2.0")
    cal.add("method", method)
    return cal


def _add_common_props(event, session: schemas.Session):
    event.add("uid", session.id)
    event.add("summary", session.title)
    event.add("dtstart", _replace_tz(session.start_time))
    event.add("dtend", _replace_tz(session.end_time))
    event.add("class", "PUBLIC")
    event.add("description", _make_description(session))


def _add_attendee(event, user_email):
    attendee = vCalAddress(f"MAILTO:{user_email}")
    attendee.params["ROLE"] = vText("REQ-PARTICIPANT")
    attendee.params["PARTSTAT"] = vText("NEEDS-ACTION")
    attendee.params["RSVP"] = vBoolean(False)
    event.add("attendee", attendee, encode=0)


def _add_url(event, session: schemas.Session):
    uri = vUri(_make_url(session))
    event.add("url", uri)


def _make_url(session: schemas.Session):
    return f"https://{settings.year}.javazone.no/program/{session.id}"


if __name__ == "__main__":

    def main_test():
        s = schemas.Session.model_validate(
            {
                "id": "1234",
                "title": "Test session title",
                "startTime": "20241010T100000",
                "endTime": "20241010T110000",
                "abstract": "Test session abstract",
                "room": "Test room",
            }
        )
        print("==== INVITE ====")
        cal = _create_invite(s, "mortenjo@ifi.uio.no")
        print(cal.to_ical().decode("utf-8"))
        print("==== CANCEL ====")
        cal = _create_cancel(s, "mortenjo@ifi.uio.no")
        print(cal.to_ical().decode("utf-8"))

    main_test()
