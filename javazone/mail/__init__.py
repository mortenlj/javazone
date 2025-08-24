import logging
from datetime import datetime

from fastapi import Request
from icalendar import Calendar, vCalAddress, vText, vBoolean
from sqlalchemy import select
from sqlalchemy.orm import Session

from javazone.core import config
from javazone.core.config import settings
from javazone.database import models
from javazone.database.models import EmailQueue
from javazone.http import schemas
from javazone.ics import create_calendar
from javazone.mail import maileroo
from javazone.mail import sendgrid

LOG = logging.getLogger(__name__)


async def process_queue(req: Request, db: Session):
    def url_for(i):
        return f"Leave here: {req.url_for('leave_session', id=i)}"

    stmt = select(EmailQueue).where(EmailQueue.sent_at.is_(None)).order_by(EmailQueue.scheduled_at).limit(30)
    for eq in db.scalars(stmt):
        LOG.debug("Processing email queue item %r", eq)
        session = schemas.Session.model_validate_json(eq.data)
        match eq.action:
            case models.Action.INVITE:
                send_invite(eq, session, url_for)
            case models.Action.CANCEL:
                send_cancel(eq, session)
            case models.Action.UPDATE:
                send_update(eq, session, url_for)
            case _:
                LOG.error("Unknown action %r", eq.action)
                continue
        eq.sent_at = datetime.now()
        db.add(eq)
        db.commit()


def send_update(eq, session, url_for):
    send_invite(eq, session, url_for)


def send_cancel(eq: EmailQueue, session: schemas.Session):
    LOG.info("Sending cancel to %s for session %s", eq.user_email, session.id)
    invite = _create_cancel(session, eq.user_email)
    title = f"Cancelled: {session.title}"
    _send_message(eq, title, invite)


def send_invite(eq: EmailQueue, session: schemas.Session, url_for):
    if any(v is None for v in (session.start_time, session.end_time)):
        LOG.warning("Can't send invite for Session %s (%s), it is missing required fields", session.id, session.title)
        return
    LOG.info("Sending invite to %s for session %s", eq.user_email, session.id)
    invite = _create_invite(session, eq.user_email, url_for)
    _send_message(eq, session.title, invite)


def _send_message(eq: EmailQueue, title: str, invite: Calendar):
    if settings.mail.provider == config.MailProvider.SEND_GRID:
        sendgrid.send_message(eq, title, invite)
    elif settings.mail.provider == config.MailProvider.MAILEROO:
        maileroo.send_message(eq, title, invite)
    else:
        LOG.error("No mail provider selected! Cannot send email to %s", eq.user_email)


def _create_cancel(session: schemas.Session, user_email: str) -> Calendar:
    cal = create_calendar("CANCEL")
    event = session.event(status="CANCELLED", transparency="TRANSPARENT", priority=1)
    _add_attendee(event, user_email)
    cal.add_component(event)

    return cal


def _create_invite(session: schemas.Session, user_email: str, url_for) -> Calendar:
    cal = create_calendar("REQUEST")
    event = session.event(status="CONFIRMED", transparency="OPAQUE", priority=5, with_alarm=True, url_for=url_for)
    _add_attendee(event, user_email)
    cal.add_component(event)

    return cal


def _add_attendee(event, user_email):
    attendee = vCalAddress(f"MAILTO:{user_email}")
    attendee.params["ROLE"] = vText("REQ-PARTICIPANT")
    attendee.params["PARTSTAT"] = vText("NEEDS-ACTION")
    attendee.params["RSVP"] = vBoolean(False)
    event.add("attendee", attendee, encode=0)


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
