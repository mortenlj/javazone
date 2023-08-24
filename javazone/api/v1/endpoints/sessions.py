import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

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


@router.post(
    "/",
    response_model=schemas.Session,
    name="Create session",
)
def post_session(session: schemas.Session, db: Session = Depends(get_db)):
    db_session = models.Session(**session.dict())
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    return db_session


@router.put("/{id}", response_model=schemas.Session, name="Update session")
def put_session(id: uuid.UUID, session: schemas.Session, db: Session = Depends(get_db)):
    db_session: models.Session = db.query(models.Session).filter(models.Session.id == id).first()
    if db_session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    for field in session.__fields_set__:
        setattr(db_session, field, getattr(session, field))
    db.merge(db_session)
    db.commit()
    db.refresh(db_session)
    return db_session


@router.get(
    "/{id}",
    response_model=schemas.Session,
)
def get_session(id: uuid.UUID, db: Session = Depends(get_db)):
    db_session: models.Session = db.query(models.Session).filter(models.Session.id == id).first()
    if db_session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return db_session
