import uuid
from typing import Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from javazone.database import models


def get_all(db: Session) -> list[models.Session]:
    return db.query(models.Session).all()


def get(id: uuid.UUID, db: Session) -> models.Session:
    db_session: Optional[models.Session] = db.query(models.Session).filter(models.Session.id == id).first()
    if db_session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return db_session


def update(id: uuid.UUID, user: models.User, db: Session) -> models.Session:
    db_session: Optional[models.Session] = db.query(models.Session).filter(models.Session.id == id).first()
    if db_session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    try:
        eq = models.EmailQueue(user_email=user.email, data=db_session.data, action=models.Action.UPDATE)
        db.add(eq)
        db.commit()
    except ValueError:
        pass
    return db_session


def join(id: uuid.UUID, user: models.User, db: Session) -> models.Session:
    db_session: Optional[models.Session] = db.query(models.Session).filter(models.Session.id == id).first()
    if db_session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    try:
        db_session.users.append(user)
        eq = models.EmailQueue(user_email=user.email, data=db_session.data, action=models.Action.INVITE)
        db.add(eq)
        db.commit()
    except ValueError:
        pass
    return db_session


def leave(id: uuid.UUID, user: models.User, db: Session) -> models.Session:
    db_session: Optional[models.Session] = db.query(models.Session).filter(models.Session.id == id).first()
    if db_session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    try:
        db_session.users.remove(user)
        eq = models.EmailQueue(user_email=user.email, data=db_session.data, action=models.Action.CANCEL)
        db.add(eq)
        db.commit()
    except ValueError:
        pass
    return db_session
