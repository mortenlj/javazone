import logging

from javazone.mail.smtp import send_message
from javazone.http import schemas
from javazone.database import models
from javazone.mail import _create_invite
from hashlib import sha256
import uuid


if __name__ == "__main__":

    def main_test():
        s = schemas.Session.model_validate(
            {
                "id": uuid.uuid4(),
                "conferenceId": uuid.uuid4(),
                "intendedAudience": "everyone",
                "length": 10,
                "format": "presentation",
                "language": "no",
                "speakers": [{"name": "Speaker One"}, {"name": "Øyvind Bærlevåg"}],
                "title": "Test session title",
                "abstract": "Test session abstract",
                "room": "Test room",
                "startTime": "2025-10-10T10:00:00",
                "endTime": "2025-10-10T11:00:00",
            }
        )
        invite = _create_invite(s, "mortenjo@ifi.uio.no", None)
        session_data = s.model_dump_json()
        session_hash = sha256(session_data.encode("utf-8")).hexdigest()
        db_session = models.Session(id=uuid.uuid4(), hash=session_hash, data=session_data)
        eq = models.EmailQueue(user_email="mortenjo@ifi.uio.no", data=db_session.data, action=models.Action.INVITE)

        send_message(eq, s.title, invite)

    logging.basicConfig(level=logging.DEBUG, format="%(asctime)s %(levelname)s %(message)s")
    main_test()
