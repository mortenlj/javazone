import uuid

from fastapi import APIRouter, Request, Depends, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from javazone.database import models
from javazone.http.deps import get_db, get_current_user
from javazone.services import sessions

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/{id}/join", status_code=status.HTTP_200_OK, response_class=HTMLResponse)
def join_session_widget(
    id: uuid.UUID, request: Request, user: models.User = Depends(get_current_user), db: Session = Depends(get_db)
):
    session = sessions.join(id, user, db)
    return templates.TemplateResponse(
        request=request,
        name="widgets/session_join_leave.html.j2",
        context={
            "session": session,
            "user": user,
        },
    )


@router.get("/{id}/leave", status_code=status.HTTP_200_OK, response_class=HTMLResponse)
def leave_session_widget(
    id: uuid.UUID, request: Request, user: models.User = Depends(get_current_user), db: Session = Depends(get_db)
):
    session = sessions.leave(id, user, db)
    return templates.TemplateResponse(
        request=request,
        name="widgets/session_join_leave.html.j2",
        context={
            "session": session,
            "user": user,
        },
    )
