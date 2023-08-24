from .base import CRUDBase
from ..database import models


class CRUDUser(CRUDBase[models.User]):
    ...


class CRUDSession(CRUDBase[models.Session]):
    ...


user = CRUDUser(models.User)
session = CRUDSession(models.Session)
