from typing import Optional

from sqlalchemy.orm import Session

from javazone.database import models
from javazone.http import schemas


def create_user(user: schemas.AuthenticatedUser, db: Session) -> models.User:
    db_user = models.User(email=user.email, name=user.name, picture_url=str(user.picture_url))
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def get_user(user: schemas.AuthenticatedUser, db: Session) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.email == user.email).first()


def delete_user(user: schemas.User, db: Session):
    db.delete(user)
    db.commit()
