import logging
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError
from sqlalchemy.orm import Session

from javazone.database import get_session, models
from javazone.security import decode_token

LOG = logging.getLogger(__name__)


token_auth_scheme = HTTPBearer()


def get_db():
    db = get_session()
    try:
        yield db
    finally:
        db.close()


async def get_current_user(
    token: Annotated[HTTPAuthorizationCredentials, Depends(token_auth_scheme)], db: Session = Depends(get_db)
):
    email = await get_authenticated_email(token)
    db_user = db.query(models.User).filter(models.User.email == email).first()
    if db_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return db_user


async def get_authenticated_email(token: Annotated[HTTPAuthorizationCredentials, Depends(token_auth_scheme)]):
    try:
        claims = await decode_token(token.credentials)
        return claims["email"]
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e
