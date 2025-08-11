from fastapi import APIRouter, Request, status, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from javazone.http import schemas
from javazone.http.deps import get_current_user

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/profile", status_code=status.HTTP_200_OK, response_class=HTMLResponse)
def profile(request: Request, user: schemas.User = Depends(get_current_user)):
    return templates.TemplateResponse(
        request=request,
        name="widgets/profile.html.j2",
        context={"user": user},
    )
