import logging
from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from javazone.database import get_session
from javazone.security import decode_token


LOG = logging.getLogger(__name__)


token_auth_scheme = HTTPBearer()


async def get_current_user(token: Annotated[HTTPAuthorizationCredentials, Depends(token_auth_scheme)]):
    claims = await decode_token(token.credentials)
    LOG.debug("Claims: %s", claims)
    return claims["email"]


def get_db():
    db = get_session()
    try:
        yield db
    finally:
        db.close()
