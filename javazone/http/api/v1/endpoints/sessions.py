import uuid
from typing import List

from fastapi import APIRouter, Depends, BackgroundTasks, Response, Request
from icalendar import Calendar
from sqlalchemy.orm import Session

from javazone import sleepingpill
from javazone.database import models
from javazone.http import schemas
from javazone.http.deps import get_db, get_current_user
from javazone.ics import create_calendar
from javazone.services import sessions

router = APIRouter(
    responses={404: {"detail": "Not found"}},
)


class CalendarResponse(Response):
    media_type = "text/calendar; method=PUBLISH"


@router.get(
    "",
    response_model=List[schemas.Session],
)
def get_sessions(db: Session = Depends(get_db)) -> list[schemas.Session]:
    """List all sessions"""
    return [schemas.Session.model_validate_json(s.data) for s in sessions.get_all(db)]


@router.get(
    ".ics",
    response_model=None,
    response_class=CalendarResponse,
)
def get_sessions_ics(req: Request, db: Session = Depends(get_db)) -> Calendar:
    """Return calendar with all sessions"""
    cal = create_calendar("PUBLISH")
    for session in (schemas.Session.from_db_session(s) for s in sessions.get_all(db)):
        cal.add_component(session.event(url_for=lambda i: f"Join here: {req.url_for("join_session_web", id=i)}"))
    return cal.to_ical()


@router.get(
    "/{id}",
    response_model=schemas.Session,
)
def get_session(id: uuid.UUID, db: Session = Depends(get_db)) -> schemas.Session:
    return schemas.Session.from_db_session(sessions.get(id, db))


@router.get(
    "/{id}/join",
    response_model=schemas.SessionWithUsers,
    response_model_exclude_unset=True,
)
def join_session(
    id: uuid.UUID,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> schemas.SessionWithUsers:
    return schemas.SessionWithUsers.from_db_session(sessions.join(id, user, db))


@router.get(
    "/{id}/leave",
    response_model=schemas.SessionWithUsers,
    response_model_exclude_unset=True,
)
def leave_session(
    id: uuid.UUID, user: models.User = Depends(get_current_user), db: Session = Depends(get_db)
) -> schemas.SessionWithUsers:
    return schemas.SessionWithUsers.from_db_session(sessions.leave(id, user, db))


@router.post("", name="Update sessions", status_code=204)
def update_sessions(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    background_tasks.add_task(sleepingpill.update_sessions, db)
