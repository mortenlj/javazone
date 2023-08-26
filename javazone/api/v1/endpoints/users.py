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


@router.post("/", response_model=schemas.User, name="Create user", status_code=201)
def post_user(email: str, db: Session = Depends(get_db)):
    db_user = models.User(email=email)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@router.delete("/{id}", name="Delete user", status_code=204)
def delete_user(email: str, db: Session = Depends(get_db)):
    db_user: models.User = db.query(models.User).filter(models.User.email == email).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(db_user)
    db.commit()
    return


@router.get(
    "/{id}",
    response_model=schemas.User,
)
def get_user(email: str, db: Session = Depends(get_db)):
    db_user: models.User = db.query(models.User).filter(models.User.email == email).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user
