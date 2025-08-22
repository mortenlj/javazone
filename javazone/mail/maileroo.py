import logging

from maileroo import MailerooClient, EmailAddress, Attachment

from javazone.core.config import settings

LOG = logging.getLogger(__name__)


class MailerooException(Exception):
    pass


def enabled():
    return settings.maileroo.api_key is not None and settings.maileroo.sender_email is not None


def send_message(eq, title, invite):
    mime_type = f"text/calendar;method={invite.get("method")}"
    bytes = invite.to_ical()
    body = Attachment.from_content("", bytes.decode("utf-8"), mime_type, inline=True, is_base64=False)
    attachment = Attachment.from_content("event.ics", bytes.decode("utf-8"), mime_type)

    message = {
        "from": EmailAddress(settings.sendgrid.sender_email),
        "to": EmailAddress(eq.user_email),
        "subject": title,
        "attachments": [body, attachment],
        "plain": bytes.decode("utf-8"),
    }

    if not enabled():
        LOG.info("Send is disabled! Would have sent email %s", message)
        LOG.debug("iCalendar:\n%s", bytes.decode("utf-8"))
        return
    maileroo = MailerooClient(settings.maileroo.api_key.get_secret_value())
    try:
        reference_id = maileroo.send_basic_email(message)
        LOG.info("Email sent successfully with reference ID: %s", reference_id)
    except ValueError as e:
        raise MailerooException(f"Invalid email data: {e}") from e
    except RuntimeError as e:
        raise MailerooException("Failed to send email") from e
