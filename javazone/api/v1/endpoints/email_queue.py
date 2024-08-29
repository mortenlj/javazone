from fastapi import APIRouter, Depends, status, BackgroundTasks, Request
from sqlalchemy.orm import Session

from javazone import mail
from javazone.api.deps import get_db

router = APIRouter(
    responses={status.HTTP_404_NOT_FOUND: {"detail": "Not found"}},
)


@router.post("", name="Process queue", status_code=204)
def process_queue(req: Request, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    background_tasks.add_task(mail.process_queue, req, db)
