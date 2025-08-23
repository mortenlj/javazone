import logging
from pprint import pformat
from typing import Annotated

from authlib.jose import JoseError
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from javazone.core.config import settings
from javazone.database import get_session
from javazone.http import schemas
from javazone.security import decode_token
from javazone.services import users

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
    db_user = users.get_user(user, db)
    if db_user is None:
        db_user = users.create_user(user, db)
    return db_user


async def get_authenticated_user(
    token: Annotated[HTTPAuthorizationCredentials, Depends(token_auth_scheme)],
) -> schemas.AuthenticatedUser:
    if settings.debug:
        LOG.warning("Running in debug mode, using %s as authenticated user", settings.oauth.client_id)
        return schemas.AuthenticatedUser(email=settings.oauth.client_id, name="Debug User")
    try:
        claims = await decode_token(token.credentials)
        LOG.debug("Decoded token claims:\n%s", pformat(claims))
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
