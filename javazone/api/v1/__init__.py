from fastapi import APIRouter

from .endpoints import users
from .endpoints import sessions

router = APIRouter()
router.include_router(users.router, prefix="/user", tags=["user"])
router.include_router(sessions.router, prefix="/sessions", tags=["session"])
