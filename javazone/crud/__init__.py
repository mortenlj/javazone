from .base import CRUDBase
from ..database import models


class CRUDTeam(CRUDBase[models.Team]):
    ...


team = CRUDTeam(models.Team)
