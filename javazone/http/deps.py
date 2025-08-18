import logging
from pprint import pformat
from typing import Annotated

from authlib.jose import JoseError
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from javazone.core.config import settings
from javazone.database import get_session, models
from javazone.http import schemas
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
    user = await get_authenticated_user(token)
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unknown user",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return db_user


async def get_authenticated_user(
    token: Annotated[HTTPAuthorizationCredentials, Depends(token_auth_scheme)],
) -> schemas.AuthenticatedUser:
    if settings.debug:
        LOG.warning("Running in debug mode, using %s as authenticated user", settings.oauth.client_id)
        return schemas.AuthenticatedUser(email=settings.oauth.client_id, name="Debug User")
    try:
        claims = await decode_token(token.credentials)
        LOG.info("Decoded token claims:\n%s", pformat(claims))
        if "email" not in claims:
            LOG.error("Missing email claim in token: %s", claims)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing email claim in token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return schemas.AuthenticatedUser(
            email=claims["email"], name=claims.get("name", ""), picture_url=claims.get("picture")
        )
    except JoseError as e:
        LOG.error("Failed to decode token: %s", e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e
