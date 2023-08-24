import uuid
from typing import (
    Generic,
    List,
    Optional,
    Type,
    TypeVar,
    Protocol,
    Set,
    Dict,
)

from sqlalchemy.orm import Session

from javazone.database.models import Common

NOTSET = object()

ModelType = TypeVar("ModelType", bound=Common)


class Convertible(Protocol):
    @classmethod
    def fields(cls) -> Set[str]:
        ...


class CRUDBase(Generic[ModelType]):
    def __init__(self, model: Type[ModelType]):
        """
        CRUD object with default methods to Create, Read, Update, Delete (CRUD).
        **Parameters**
        * `model`: A SQLAlchemy model class
        """
        self.model = model

    def _convert(self, instance: Convertible) -> ModelType:
        data = self._get_data(instance)
        return self.model(**data)

    def _get_data(self, instance: Convertible) -> Dict:
        target_fields = self.model.fields()
        source_fields = instance.fields()
        fields = target_fields & source_fields
        return {
            field: getattr(instance, field)
            for field in fields
            if getattr(instance, field) is not NOTSET
        }

    def get(self, db: Session, id: uuid.UUID) -> Optional[ModelType]:
        return db.query(self.model).filter(self.model.id == id).first()

    def get_multi(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> List[ModelType]:
        return db.query(self.model).offset(skip).limit(limit).all()

    def create(self, db: Session, *, obj_in: Convertible) -> ModelType:
        db_obj = self._convert(obj_in)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(
        self, db: Session, *, db_obj: ModelType, obj_in: Convertible
    ) -> ModelType:
        update_data = self._get_data(obj_in)
        for field in update_data:
            setattr(db_obj, field, update_data[field])
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def remove(self, db: Session, *, id: uuid.UUID) -> ModelType:
        obj = db.query(self.model).get(id)
        db.delete(obj)
        db.commit()
        return obj
