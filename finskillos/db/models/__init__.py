"""ORM model package for FinSkillOS core domain.

Importing this module registers every Base subclass with the shared
metadata so Alembic autogenerate and `Base.metadata.create_all` see the
full schema.
"""

from finskillos.db.models.account import Account
from finskillos.db.models.alert import Alert
from finskillos.db.models.portfolio import PortfolioSnapshot
from finskillos.db.models.position import Position
from finskillos.db.models.trade import Trade

__all__ = [
    "Account",
    "Alert",
    "PortfolioSnapshot",
    "Position",
    "Trade",
]
