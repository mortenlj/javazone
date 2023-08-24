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
    response_model=List[schemas.User],
)
def get_users(db: Session = Depends(get_db)):
    """List all users"""
    return db.query(models.User).all()


@router.post(
    "/",
    response_model=schemas.User,
    name="Create user",
)
def post_user(user: schemas.User, db: Session = Depends(get_db)):
    db_user = models.User(**user.dict())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@router.put("/{id}", response_model=schemas.User, name="Update user")
def put_user(id: uuid.UUID, user: schemas.User, db: Session = Depends(get_db)):
    db_user: models.User = db.query(models.User).filter(models.User.id == id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    for field in user.__fields_set__:
        setattr(db_user, field, getattr(user, field))
    db.merge(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@router.get(
    "/{id}",
    response_model=schemas.User,
)
def get_user(id: uuid.UUID, db: Session = Depends(get_db)):
    db_user: models.User = db.query(models.User).filter(models.User.id == id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user
