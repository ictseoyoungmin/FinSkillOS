"""ORM model package for FinSkillOS core domain.

Importing this module registers every Base subclass with the shared
metadata so Alembic autogenerate and `Base.metadata.create_all` see the
full schema.
"""

from finskillos.db.models.account import Account
from finskillos.db.models.alert import Alert
from finskillos.db.models.event import Event, EventLink
from finskillos.db.models.indicator import IndicatorSnapshot
from finskillos.db.models.market import MarketBar
from finskillos.db.models.news import NewsArticle, NewsImpact
from finskillos.db.models.portfolio import PortfolioSnapshot
from finskillos.db.models.position import Position
from finskillos.db.models.regime import MarketRegime
from finskillos.db.models.symbol_logo import SymbolLogoCache
from finskillos.db.models.symbol_subscription import SymbolSubscription
from finskillos.db.models.symbol_subscription_folder import (
    SymbolSubscriptionFolder,
    SymbolSubscriptionFolderMembership,
)
from finskillos.db.models.system_ops import SystemOpsProtocolRun, WorkerCycleRun
from finskillos.db.models.trade import Trade

__all__ = [
    "Account",
    "Alert",
    "Event",
    "EventLink",
    "IndicatorSnapshot",
    "MarketBar",
    "MarketRegime",
    "NewsArticle",
    "NewsImpact",
    "PortfolioSnapshot",
    "Position",
    "SymbolLogoCache",
    "SymbolSubscription",
    "SymbolSubscriptionFolder",
    "SymbolSubscriptionFolderMembership",
    "SystemOpsProtocolRun",
    "Trade",
    "WorkerCycleRun",
]
