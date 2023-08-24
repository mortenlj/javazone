from fastapi import APIRouter

from .endpoints import teams

router = APIRouter()
router.include_router(teams.router, prefix="/teams", tags=["teams"])
