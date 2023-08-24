import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from console.api import schemas
from console.api.deps import get_db
from console.database import models

router = APIRouter(
    responses={404: {"detail": "Not found"}},
)


@router.get(
    "/",
    response_model=List[schemas.Team],
)
def get_teams(db: Session = Depends(get_db)):
    """List all teams"""
    return db.query(models.Team).all()


@router.post(
    "/",
    response_model=schemas.Team,
    name="Create team",
)
def post_team(team: schemas.Team, db: Session = Depends(get_db)):
    db_team = models.Team(**team.dict())
    db.add(db_team)
    db.commit()
    db.refresh(db_team)
    return db_team


@router.put("/{id}", response_model=schemas.Team, name="Update team")
def put_team(id: uuid.UUID, team: schemas.Team, db: Session = Depends(get_db)):
    db_team: models.Team = db.query(models.Team).filter(models.Team.id == id).first()
    if db_team is None:
        raise HTTPException(status_code=404, detail="Team not found")
    for field in team.__fields_set__:
        setattr(db_team, field, getattr(team, field))
    db.merge(db_team)
    db.commit()
    db.refresh(db_team)
    return db_team


@router.get(
    "/{id}",
    response_model=schemas.Team,
)
def get_team(id: uuid.UUID, db: Session = Depends(get_db)):
    db_team: models.Team = db.query(models.Team).filter(models.Team.id == id).first()
    if db_team is None:
        raise HTTPException(status_code=404, detail="Team not found")
    return db_team
