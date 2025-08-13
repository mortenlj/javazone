import random

from fastapi import APIRouter, Request, status, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from .widgets import router as widgets_router
from javazone.http.deps import get_db
from .. import schemas
from ...database import models

router = APIRouter()
router.include_router(widgets_router, prefix="/widgets", tags=["widgets"])

templates = Jinja2Templates(directory="templates")


@router.get("/", status_code=status.HTTP_200_OK, response_class=HTMLResponse)
def index(request: Request, db: Session = Depends(get_db)):
    all_sessions = [schemas.Session.model_validate_json(s.data) for s in db.query(models.Session).all()]
    sessions = {
        "tuesday": [],
        "wednesday": [],
        "thursday": [],
    }
    for session in all_sessions:
        if session.start_time is None:
            day = random.choice(["tuesday", "wednesday", "thursday"])
            sessions[day].append(session)
        elif session.start_time.weekday() == 1:
            sessions["tuesday"].append(session)
        elif session.start_time.weekday() == 2:
            sessions["wednesday"].append(session)
        elif session.start_time.weekday() == 3:
            sessions["thursday"].append(session)
    return templates.TemplateResponse(
        request=request,
        name="index.html.j2",
        context={
            "sessions": sessions,
        },
    )


@router.get("/login", status_code=status.HTTP_200_OK, response_class=RedirectResponse)
def login(request: Request):
    return RedirectResponse(request.url_for("index"), status_code=status.HTTP_302_FOUND)
