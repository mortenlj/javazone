import datetime
import uuid
from typing import Optional, Set, Type, List

import strawberry
from fastapi import Depends
from strawberry.fastapi import GraphQLRouter
from strawberry.types import Info

from console import crud
from console.api.deps import get_db
from console.crud.base import NOTSET
from console.database import models


async def get_context(db=Depends(get_db)):
    return {"db": db}


class MappingHelper:
    @classmethod
    def fields(cls) -> Set[str]:
        return {f.name for f in cls._type_definition.fields}


def convert(db_obj: models.Base, cls: Type[MappingHelper]) -> MappingHelper:
    target_fields = cls.fields()
    source_fields = db_obj.fields()
    fields = target_fields & source_fields
    data = {field: getattr(db_obj, field) for field in fields}
    return cls(**data)


@strawberry.input
class TeamInput(MappingHelper):
    slug: str
    name: str
    purpose: Optional[str] = NOTSET


@strawberry.type
class TeamOutput(MappingHelper):
    id: uuid.UUID
    created_at: Optional[datetime.datetime]
    updated_at: Optional[datetime.datetime]
    deleted_at: Optional[datetime.datetime]
    created_by_id: Optional[uuid.UUID]
    updated_by_id: Optional[uuid.UUID]
    deleted_by_id: Optional[uuid.UUID]
    slug: str
    name: str
    purpose: Optional[str]


@strawberry.type
class Query:
    @strawberry.field
    def get_team(self, id: uuid.UUID, info: Info) -> Optional[TeamOutput]:
        db = info.context["db"]
        db_team = crud.team.get(db, id)
        if db_team is None:
            # TODO: Do error handling
            return None
        return convert(db_team, TeamOutput)

    @strawberry.field
    def get_teams(self, info: Info) -> List[TeamOutput]:
        db = info.context["db"]
        db_teams = crud.team.get_multi(db)
        return [convert(db_team, TeamOutput) for db_team in db_teams]


@strawberry.type(description="Mutate teams")
class TeamMutation:
    @strawberry.mutation(description="Create a team")
    def create_team(self, team: TeamInput, info: Info) -> TeamOutput:
        db = info.context["db"]
        db_team = crud.team.create(db, obj_in=team)
        return convert(db_team, TeamOutput)

    @strawberry.mutation(description="Update a team")
    def update_team(self, id: uuid.UUID, team: TeamInput, info: Info) -> TeamOutput:
        db = info.context["db"]
        db_team = crud.team.get(db, id)
        if db_team is None:
            # TODO: Do error handling
            return None
        db_team = crud.team.update(db, db_obj=db_team, obj_in=team)
        return convert(db_team, TeamOutput)


schema = strawberry.Schema(query=Query, mutation=TeamMutation)
graphql_app = GraphQLRouter(schema, context_getter=get_context)
