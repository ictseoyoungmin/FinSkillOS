from dataclasses import dataclass
from decimal import Decimal
import csv
from pathlib import Path


@dataclass(frozen=True)
class PortfolioPositionInput:
    symbol: str
    name: str
    sector: str
    quantity: Decimal
    market_value: Decimal
    cost_basis: Decimal | None = None


@dataclass(frozen=True)
class PortfolioSummary:
    total_value: Decimal
    position_count: int
    largest_position_symbol: str | None
    largest_position_weight: Decimal


def load_portfolio_csv(path: str | Path) -> list[PortfolioPositionInput]:
    positions: list[PortfolioPositionInput] = []
    with Path(path).open(newline="", encoding="utf-8") as csv_file:
        for row in csv.DictReader(csv_file):
            positions.append(
                PortfolioPositionInput(
                    symbol=row["symbol"].strip().upper(),
                    name=row.get("name", "").strip(),
                    sector=row.get("sector", "").strip(),
                    quantity=Decimal(row.get("quantity", "0")),
                    market_value=Decimal(row.get("market_value", "0")),
                    cost_basis=Decimal(row["cost_basis"]) if row.get("cost_basis") else None,
                )
            )
    return positions


def summarize_positions(positions: list[PortfolioPositionInput]) -> PortfolioSummary:
    total_value = sum((position.market_value for position in positions), Decimal("0"))
    if not positions or total_value == 0:
        return PortfolioSummary(Decimal("0"), len(positions), None, Decimal("0"))

    largest = max(positions, key=lambda position: position.market_value)
    return PortfolioSummary(
        total_value=total_value,
        position_count=len(positions),
        largest_position_symbol=largest.symbol,
        largest_position_weight=largest.market_value / total_value,
    )
