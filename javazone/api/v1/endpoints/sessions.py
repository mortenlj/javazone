import json
import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from javazone import sleepingpill
from javazone.api import schemas
from javazone.api.deps import get_db, get_current_user
from javazone.database import models

router = APIRouter(
    responses={404: {"detail": "Not found"}},
)


@router.get(
    "/",
    response_model=List[dict],
)
def get_sessions(db: Session = Depends(get_db)) -> list[dict]:
    """List all sessions"""
    return [json.loads(s.data) for s in db.query(models.Session).all()]


@router.get(
    "/{id}",
    response_model=schemas.Session,
)
def get_session(id: uuid.UUID, db: Session = Depends(get_db)) -> schemas.Session:
    db_session: models.Session = db.query(models.Session).filter(models.Session.id == id).first()
    if db_session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return db_session


@router.post(
    "/{id}/join",
    response_model=schemas.Session,
)
def join_session(
    id: uuid.UUID, user: schemas.User = Depends(get_current_user), db: Session = Depends(get_db)
) -> schemas.Session:
    db_session: models.Session = db.query(models.Session).filter(models.Session.id == id).first()
    if db_session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    if user not in db_session.users:
        db_session.users.append(user)
        db.commit()
    return db_session


@router.post(
    "/{id}/leave",
    response_model=schemas.Session,
)
def leave_session(
    id: uuid.UUID, user: schemas.User = Depends(get_current_user), db: Session = Depends(get_db)
) -> schemas.Session:
    db_session: models.Session = db.query(models.Session).filter(models.Session.id == id).first()
    if db_session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    try:
        db_session.users.remove(user)
        db.commit()
    except ValueError:
        pass
    return db_session


@router.post("/", name="Update sessions", status_code=204)
def update_sessions(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    background_tasks.add_task(sleepingpill.update_sessions, db)
