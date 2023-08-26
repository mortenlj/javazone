import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from javazone import sleepingpill
from javazone.api import schemas
from javazone.api.deps import get_db
from javazone.database import models

router = APIRouter(
    responses={404: {"detail": "Not found"}},
)


@router.get(
    "/",
    response_model=List[schemas.Session],
)
def get_sessions(db: Session = Depends(get_db)):
    """List all sessions"""
    return db.query(models.Session).all()


@router.get(
    "/{id}",
    response_model=schemas.Session,
)
def get_session(id: uuid.UUID, db: Session = Depends(get_db)):
    db_session: models.Session = (
        db.query(models.Session).filter(models.Session.id == id).first()
    )
    if db_session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return db_session


@router.post("/", name="Update sessions", status_code=204)
def update_sessions(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    background_tasks.add_task(sleepingpill.update_sessions, db)
