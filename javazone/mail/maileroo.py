import logging

from maileroo import MailerooClient, EmailAddress, Attachment

from javazone.core.config import settings

LOG = logging.getLogger(__name__)


class MailerooException(Exception):
    pass


def enabled():
    return settings.mail.maileroo.api_key is not None and settings.mail.sender_email is not None


def send_message(eq, title, invite):
    mime_type = f"text/calendar;method={invite.get("method")}"
    bytes = invite.to_ical()
    inline = Attachment.from_content("event_inline.ics", bytes.decode("utf-8"), mime_type, inline=True, is_base64=False)
    attachment = Attachment.from_content("event.ics", bytes.decode("utf-8"), mime_type)

    message = {
        "from": EmailAddress(settings.mail.sender_email, "JavaZone Calender Manager"),
        "to": EmailAddress(eq.user_email),
        "subject": title,
        "attachments": [inline, attachment],
        "plain": title,
    }

    if not enabled():
        LOG.info("Send is disabled! Would have sent email %s", message)
        LOG.debug("iCalendar:\n%s", bytes.decode("utf-8"))
        return
    maileroo = MailerooClient(settings.mail.maileroo.api_key.get_secret_value())
    try:
        reference_id = maileroo.send_basic_email(message)
        LOG.info("Email sent successfully with reference ID: %s", reference_id)
    except ValueError as e:
        raise MailerooException(f"Invalid email data: {e}") from e
    except RuntimeError as e:
        raise MailerooException("Failed to send email") from e
