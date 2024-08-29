import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Response, Request
from icalendar import Calendar
from sqlalchemy.orm import Session

from javazone import sleepingpill
from javazone.api import schemas
from javazone.api.deps import get_db, get_current_user
from javazone.database import models
from javazone.ics import create_calendar

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
    return [schemas.Session.model_validate_json(s.data) for s in db.query(models.Session).all()]


@router.get(
    ".ics",
    response_model=None,
    response_class=CalendarResponse,
)
def get_sessions_ics(req: Request, db: Session = Depends(get_db)) -> Calendar:
    """Return calendar with all sessions"""
    cal = create_calendar("PUBLISH")
    for session in (schemas.Session.model_validate_json(s.data) for s in db.query(models.Session).all()):
        cal.add_component(session.event(url_for=lambda i: req.url_for("join_session", id=i)))
    return cal.to_ical()


@router.get(
    "/{id}",
    response_model=schemas.Session,
)
def get_session(id: uuid.UUID, db: Session = Depends(get_db)) -> schemas.SessionWithUsers:
    db_session: models.Session = db.query(models.Session).filter(models.Session.id == id).first()
    if db_session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return schemas.Session.model_validate_json(db_session.data)


@router.get(
    "/{id}/join",
    response_model=schemas.SessionWithUsers,
    response_model_exclude_unset=True,
)
def join_session(
    id: uuid.UUID,
    user: schemas.User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> schemas.SessionWithUsers:
    db_session: models.Session = db.query(models.Session).filter(models.Session.id == id).first()
    if db_session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    if user not in db_session.users:
        db_session.users.append(user)
        eq = models.EmailQueue(user_email=user.email, data=db_session.data, action=models.Action.INVITE)
        db.add(eq)
        db.commit()
    return schemas.SessionWithUsers.from_db_session(db_session)


@router.get(
    "/{id}/leave",
    response_model=schemas.SessionWithUsers,
    response_model_exclude_unset=True,
)
def leave_session(
    id: uuid.UUID, user: schemas.User = Depends(get_current_user), db: Session = Depends(get_db)
) -> schemas.SessionWithUsers:
    db_session: models.Session = db.query(models.Session).filter(models.Session.id == id).first()
    if db_session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    try:
        db_session.users.remove(user)
        eq = models.EmailQueue(user_email=user.email, data=db_session.data, action=models.Action.CANCEL)
        db.add(eq)
        db.commit()
    except ValueError:
        pass
    return schemas.SessionWithUsers.from_db_session(db_session)


@router.post("", name="Update sessions", status_code=204)
def update_sessions(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    background_tasks.add_task(sleepingpill.update_sessions, db)
