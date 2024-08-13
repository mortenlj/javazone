import json
import logging

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

from javazone.api import schemas
from javazone.core.config import settings
from javazone.database import models

LOG = logging.getLogger(__name__)


def send_invite(session: models.Session, user: schemas.User):
    LOG.info("Sending invite to %s for session %s", user.email, session.id)
    session_data = json.loads(session.data)
    message = Mail(
        from_email="mortenlj@altiboxmail.no",
        to_emails=user.email,
        subject=session_data["title"],
        html_content=session_data["abstract"],
    )
    try:
        sg = SendGridAPIClient(settings.sendgrid.api_key.get_secret_value())
        response = sg.send(message)
        LOG.debug(response.status_code)
        LOG.debug(response.body)
        LOG.debug(response.headers)
    except Exception as e:
        LOG.error(e.message)
