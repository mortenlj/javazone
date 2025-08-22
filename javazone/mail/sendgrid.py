import base64
import logging

from icalendar import Calendar
from sendgrid import Mail, Attachment, SendGridAPIClient

from javazone.core.config import settings
from javazone.database.models import EmailQueue

LOG = logging.getLogger(__name__)


class SendGridException(Exception):
    pass


def enabled():
    return settings.sendgrid.api_key is not None and settings.sendgrid.sender_email is not None


def send_message(eq: EmailQueue, title: str, invite: Calendar):
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

    if not enabled():
        LOG.info("Send is disabled! Would have sent email %s", message)
        LOG.debug("iCalendar:\n%s", bytes.decode("utf-8"))
        return
    sg = SendGridAPIClient(settings.sendgrid.api_key.get_secret_value())
    response = sg.send(message)
    if response.status_code < 200 or response.status_code >= 300:
        raise SendGridException(f"Failed to send email: {response.status_code} {response.body}")
