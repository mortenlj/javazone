from fastapi import APIRouter

from ibidem.javazone.http.api import v1

router = APIRouter()
router.include_router(v1.router, prefix="/v1")
