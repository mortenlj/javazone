from fastapi import APIRouter, Request, status, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from javazone.http import schemas
from javazone.http.deps import get_authenticated_user, get_db
from javazone.services import users

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/profile", status_code=status.HTTP_200_OK, response_class=HTMLResponse)
def profile(
    request: Request,
    auth_user: schemas.AuthenticatedUser = Depends(get_authenticated_user),
    db: Session = Depends(get_db),
):
    user = users.get_user(auth_user, db)
    if user is None:
        user = users.create_user(auth_user, db)
    return templates.TemplateResponse(
        request=request,
        name="widgets/profile.html.j2",
        context={"user": user},
    )
