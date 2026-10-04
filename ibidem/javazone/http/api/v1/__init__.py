from fastapi import APIRouter

from ibidem.javazone.http.api.v1.endpoints import email_queue, sessions, users

router = APIRouter()
router.include_router(users.router, prefix="/users", tags=["user"])
router.include_router(sessions.router, prefix="/sessions", tags=["session"])
router.include_router(email_queue.router, prefix="/email_queue", tags=["session"])
