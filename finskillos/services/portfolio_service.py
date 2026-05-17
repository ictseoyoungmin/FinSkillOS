"""PortfolioService — slice-03 application layer over the DB foundation.

This module exposes:

* `PortfolioPositionInput` / `load_portfolio_csv` — DB-free CSV adapter
  (matches docs/v2_1/08 §4.2 input schema; both `ticker` and the legacy
  `symbol` column header are accepted).
* `PortfolioSummary` — Mission Control read model (total value, weights,
  largest position, single-position 1천만원 limit utilization).
* `PortfolioService` — class-based facade per docs/v2_1/08 §11.1:
  `import_snapshot`, `upsert_position`, `get_current_positions`,
  `get_portfolio_summary`, `calculate_exposure`. All writes go through the
  slice-02 repositories so unique constraints and ON DELETE CASCADE stay
  in effect.

This slice does **not** generate buy/sell instructions. The summary is a
descriptive read model only.
"""

from __future__ import annotations

import csv
import uuid
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from pathlib import Path

from sqlalchemy.orm import Session

from finskillos.db.models import PortfolioSnapshot, Position
from finskillos.db.repositories import PortfolioRepository, PositionRepository

SINGLE_POSITION_LIMIT_KRW = Decimal("10000000")


@dataclass(frozen=True)
class PortfolioPositionInput:
    """Canonical CSV / API row used by import_snapshot.

    `ticker` is the primary key; `symbol` is accepted at parse time as a
    backward-compat alias for older CSV exports.
    """

    ticker: str
    quantity: Decimal
    market_value: Decimal
    name: str | None = None
    sector: str | None = None
    theme: str | None = None
    strategy_type: str = "swing"
    average_cost: Decimal | None = None
    pnl_pct: Decimal | None = None
    stop_loss: Decimal | None = None
    take_profit: Decimal | None = None
    thesis: str | None = None


@dataclass(frozen=True)
class PortfolioSummary:
    """Read model for Mission Control / Control Room cards."""

    total_value: Decimal
    cash_value: Decimal
    position_count: int
    largest_position_ticker: str | None
    largest_position_weight: Decimal
    over_single_limit_tickers: tuple[str, ...] = field(default_factory=tuple)
    sector_exposure: dict[str, Decimal] = field(default_factory=dict)


def _decimal_or_none(value: str | None) -> Decimal | None:
    if value is None:
        return None
    cleaned = value.strip()
    if cleaned == "":
        return None
    return Decimal(cleaned)


def load_portfolio_csv(path: str | Path) -> list[PortfolioPositionInput]:
    """Parse a portfolio CSV into `PortfolioPositionInput` rows.

    Accepts both the v2.1 `ticker` column (docs/v2_1/08 §4.2) and the
    legacy `symbol` column. Numeric columns are parsed as `Decimal` so
    rounding stays exact for the 1천만원 limit check.
    """

    rows: list[PortfolioPositionInput] = []
    with Path(path).open(newline="", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        for raw in reader:
            ticker_raw = (raw.get("ticker") or raw.get("symbol") or "").strip().upper()
            if not ticker_raw:
                continue
            rows.append(
                PortfolioPositionInput(
                    ticker=ticker_raw,
                    name=(raw.get("name") or "").strip() or None,
                    sector=(raw.get("sector") or "").strip() or None,
                    theme=(raw.get("theme") or "").strip() or None,
                    strategy_type=(raw.get("strategy_type") or "swing").strip() or "swing",
                    quantity=Decimal(raw.get("quantity", "0") or "0"),
                    market_value=Decimal(raw.get("market_value", "0") or "0"),
                    average_cost=_decimal_or_none(raw.get("avg_price") or raw.get("average_cost")),
                    pnl_pct=_decimal_or_none(raw.get("pnl_pct")),
                    stop_loss=_decimal_or_none(raw.get("stop_loss")),
                    take_profit=_decimal_or_none(raw.get("take_profit")),
                    thesis=(raw.get("thesis") or "").strip() or None,
                )
            )
    return rows


class PortfolioService:
    """Application-layer facade over the slice-02 portfolio repositories.

    The service does not own its own session — callers pass one in. This
    keeps it usable from both Streamlit pages (long-lived session) and the
    seed/CLI scripts (short scope via `session_scope`).
    """

    def __init__(self, session: Session) -> None:
        self.session = session
        self.positions_repo = PositionRepository(session)
        self.portfolio_repo = PortfolioRepository(session)

    # ------------------------------------------------------------------
    # Writes
    # ------------------------------------------------------------------

    def import_snapshot(
        self,
        *,
        account_id: uuid.UUID,
        snapshot_date: date,
        rows: list[PortfolioPositionInput],
        cash_value: Decimal = Decimal("0"),
        peak_value: Decimal | None = None,
        drawdown_pct: Decimal | None = None,
    ) -> PortfolioSnapshot:
        """Upsert positions and upsert the day's portfolio snapshot.

        `total_value` is derived as `sum(market_value) + cash_value` so the
        snapshot is always consistent with the position rows it represents.
        Existing positions for the same `(account_id, ticker)` are updated
        in place; tickers absent from `rows` are *not* deleted — the live
        positions table is treated as the user's current holdings.

        The portfolio_snapshots row is upserted on `(account_id,
        snapshot_date)` so same-day re-imports update the existing row
        instead of raising a unique-constraint error. Different snapshot
        dates still produce separate rows.
        """

        total_value = sum((r.market_value for r in rows), Decimal("0")) + cash_value

        for row in rows:
            self.upsert_position(account_id=account_id, row=row)

        snapshot = self.portfolio_repo.upsert_snapshot(
            account_id=account_id,
            snapshot_date=snapshot_date,
            total_value=total_value,
            cash_value=cash_value,
            peak_value=peak_value,
            drawdown_pct=drawdown_pct,
        )
        return snapshot

    def upsert_position(
        self,
        *,
        account_id: uuid.UUID,
        row: PortfolioPositionInput,
    ) -> Position:
        """Create or update a position keyed on (account_id, ticker)."""

        existing = self.positions_repo.get_by_account_and_ticker(account_id, row.ticker)
        if existing is None:
            return self.positions_repo.create(
                account_id=account_id,
                ticker=row.ticker,
                sector=row.sector,
                theme=row.theme,
                strategy_type=row.strategy_type,
                quantity=row.quantity,
                average_cost=row.average_cost,
                market_value=row.market_value,
                pnl_pct=row.pnl_pct,
                stop_loss=row.stop_loss,
                take_profit=row.take_profit,
                thesis=row.thesis,
            )

        existing.sector = row.sector if row.sector is not None else existing.sector
        existing.theme = row.theme if row.theme is not None else existing.theme
        existing.strategy_type = row.strategy_type or existing.strategy_type
        existing.quantity = row.quantity
        existing.market_value = row.market_value
        if row.average_cost is not None:
            existing.average_cost = row.average_cost
        if row.pnl_pct is not None:
            existing.pnl_pct = row.pnl_pct
        if row.stop_loss is not None:
            existing.stop_loss = row.stop_loss
        if row.take_profit is not None:
            existing.take_profit = row.take_profit
        if row.thesis is not None:
            existing.thesis = row.thesis
        self.session.flush()
        return existing

    # ------------------------------------------------------------------
    # Reads
    # ------------------------------------------------------------------

    def get_current_positions(self, account_id: uuid.UUID) -> list[Position]:
        return self.positions_repo.list_for_account(account_id)

    def get_portfolio_summary(self, account_id: uuid.UUID) -> PortfolioSummary:
        positions = self.get_current_positions(account_id)
        latest_snapshot = self.portfolio_repo.latest(account_id)

        cash_value = latest_snapshot.cash_value if latest_snapshot is not None else Decimal("0")
        positions_total = sum((p.market_value for p in positions), Decimal("0"))
        total_value = positions_total + cash_value

        if not positions or positions_total == 0:
            return PortfolioSummary(
                total_value=total_value,
                cash_value=cash_value,
                position_count=len(positions),
                largest_position_ticker=None,
                largest_position_weight=Decimal("0"),
            )

        largest = max(positions, key=lambda p: p.market_value)
        largest_weight = (
            largest.market_value / total_value if total_value > 0 else Decimal("0")
        )
        over_limit = tuple(
            p.ticker for p in positions if p.market_value > SINGLE_POSITION_LIMIT_KRW
        )

        return PortfolioSummary(
            total_value=total_value,
            cash_value=cash_value,
            position_count=len(positions),
            largest_position_ticker=largest.ticker,
            largest_position_weight=largest_weight,
            over_single_limit_tickers=over_limit,
            sector_exposure=self.calculate_exposure(account_id),
        )

    def calculate_exposure(self, account_id: uuid.UUID) -> dict[str, Decimal]:
        """Return market-value share by sector (no sector = "UNCLASSIFIED")."""

        positions = self.get_current_positions(account_id)
        total = sum((p.market_value for p in positions), Decimal("0"))
        if total == 0:
            return {}

        buckets: dict[str, Decimal] = {}
        for p in positions:
            key = p.sector or "UNCLASSIFIED"
            buckets[key] = buckets.get(key, Decimal("0")) + p.market_value

        return {k: (v / total) for k, v in buckets.items()}
