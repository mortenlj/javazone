from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from ibidem.javazone.http import schemas
from ibidem.javazone.http.deps import get_db, get_current_user
from ibidem.javazone.services import users

router = APIRouter(
    responses={status.HTTP_404_NOT_FOUND: {"detail": "Not found"}},
)


@router.get("/me", response_model=schemas.User)
def get_me(user: schemas.User = Depends(get_current_user)):
    return user


@router.delete("/me", name="Delete user", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user: schemas.User = Depends(get_current_user), db: Session = Depends(get_db)):
    users.delete_user(user, db)
