import logging
import smtplib
from email import utils, headerregistry
from email.message import EmailMessage, MIMEPart

from javazone.core.config import settings

LOG = logging.getLogger(__name__)


def enabled():
    return (
        settings.mail.smtp.username is not None
        and settings.mail.smtp.password is not None
        and settings.mail.sender_email is not None
    )


def send_message(eq, title, invite):
    msg = EmailMessage()
    msg["Subject"] = title
    msg["From"] = headerregistry.Address(display_name="JavaZone Calendar Manager", addr_spec=settings.mail.sender_email)
    msg["To"] = headerregistry.Address(addr_spec=eq.user_email)
    msg["Date"] = utils.localtime()

    msg.make_mixed()

    data = invite.to_ical()
    calendar_part = MIMEPart()
    calendar_part.set_content(
        data.decode("utf-8"), subtype="calendar", params={"method": invite.get("method")}, cte="quoted-printable"
    )
    msg.attach(calendar_part)

    msg.add_attachment(
        data.decode("utf-8"), subtype="calendar", params={"method": invite.get("method")}, filename="event.ics"
    )

    if not enabled():
        LOG.info("Send is disabled! Would have sent email\n\n%s", msg)
        return

    smtp = smtplib.SMTP_SSL(settings.mail.smtp.host)
    try:
        smtp.set_debuglevel(2 if settings.debug else 0)
        smtp.login(settings.mail.smtp.username, settings.mail.smtp.password.get_secret_value())
        smtp.send_message(msg)
        LOG.info("Email sent successfully")
    finally:
        smtp.quit()
