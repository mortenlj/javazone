from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from javazone.api import schemas
from javazone.api.deps import get_db, get_current_user, get_authenticated_email
from javazone.database import models

router = APIRouter(
    responses={status.HTTP_404_NOT_FOUND: {"detail": "Not found"}},
)


@router.post("/", response_model=schemas.User, name="Create user", status_code=status.HTTP_201_CREATED)
def post_user(email: str = Depends(get_authenticated_email), db: Session = Depends(get_db)):
    db_user = models.User(email=email)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@router.get("/me", response_model=schemas.User)
def get_me(user: schemas.User = Depends(get_current_user)):
    return user


@router.delete("/me", name="Delete user", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user: schemas.User = Depends(get_current_user), db: Session = Depends(get_db)):
    db.delete(user)
    db.commit()
    return
