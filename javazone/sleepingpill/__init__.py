import json
import logging
import uuid
from hashlib import sha256

import requests
from sqlalchemy.orm import Session

from javazone.core.config import settings
from javazone.database import models

LOG = logging.getLogger(__name__)

DATA_URL = "https://sleepingpill.javazone.no/public/allSessions/javazone_%d"


def _load_data(year):
    resp = requests.get(DATA_URL % year)
    resp.raise_for_status()
    raw_data = resp.json()
    return {uuid.UUID(session["sessionId"]): session for session in raw_data["sessions"]}


def update_sessions(db: Session):
    LOG.info("Updating sessions")
    data = _load_data(settings.year)
    db_sessions = {db_session.id: db_session for db_session in db.query(models.Session).all()}
    needs_delete = set(db_sessions.keys())
    needs_update = set()
    added = 0
    for session_id in data:
        needs_delete.remove(session_id)
        session_data = json.dumps(data[session_id], indent=None).encode("utf-8")
        session_hash = sha256(session_data).hexdigest()
        LOG.debug("Processing %s (hash: %s)", session_id, session_hash)
        db_session = db_sessions.get(session_id)
        if db_session:
            if session_hash != db_session.hash:
                db_session.data = session_data
                db_session.hash = session_hash
                needs_update.add(db_session)
        else:
            db_session = models.Session(id=session_id, hash=session_hash, data=session_data)
            db.add(db_session)
            added += 1
    for session_id in needs_delete:
        db_session = db_sessions[session_id]
        db.delete(db_session)
    db.commit()
    LOG.info("Needs to send updates for %d sessions", len(needs_update))
    LOG.info("Needs to delete %d sessions", len(needs_delete))
    LOG.info("Added %d new sessions to database", added)
