"""GoalService — DB-backed Mission Control read model.

Reads the latest portfolio_snapshots row for the account, joins it with
the account's `target_value`, and forwards the numbers to the pure
`goal_tracker.calculate_goal_status` helper. Returns a single
`GoalStatus` dataclass that matches the slice-03 core-output JSON shape.

This service is *interpretation-first*: it never recommends a trade — the
output is descriptive (progress, mode, early-stop flag) only.
"""

from __future__ import annotations

import uuid
from decimal import Decimal

from sqlalchemy.orm import Session

from finskillos.db.repositories import AccountRepository, PortfolioRepository
from finskillos.goal.goal_tracker import GoalStatus, calculate_goal_status


class GoalService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.accounts = AccountRepository(session)
        self.portfolios = PortfolioRepository(session)

    def get_goal_status(self, account_id: uuid.UUID) -> GoalStatus:
        account = self.accounts.get(account_id)
        if account is None:
            raise LookupError(f"Account {account_id} not found")

        snapshot = self.portfolios.latest(account_id)
        current_value = (
            snapshot.total_value if snapshot is not None else Decimal("0")
        )

        return calculate_goal_status(
            current_value=current_value,
            target_value=account.target_value,
        )
