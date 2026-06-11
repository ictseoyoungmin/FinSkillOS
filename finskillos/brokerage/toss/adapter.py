"""Toss read-only brokerage adapter — v4 Phase 14.

Implements the v3 ``BrokerageReadAdapter`` (Slice 200) over the Toss client:
``fetch_positions()`` maps ``GET /api/v1/holdings`` into the import-record shape
the existing confirm-gated import accepts. **No execution** — the protocol has no
order method, and this adapter adds none.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation

from finskillos.brokerage.adapter import BrokerageSnapshot
from finskillos.brokerage.toss.client import TossClient


class TossBrokerageAdapter:
    name = "toss"

    def __init__(self, client: TossClient | None = None) -> None:
        self._client = client or TossClient()

    def available(self) -> bool:
        return self._client.available()

    def fetch_positions(self) -> list[dict]:
        """Holdings → import records ``{ticker, quantity, market_value,
        average_cost, currency, name}``. Market value is the per-item evaluation
        amount in the item's own currency; ``proposal_from_records`` converts USD
        items to KRW. Empty when Toss is not configured."""

        if not self.available():
            return []
        data = self._client.holdings()
        items = data.get("items") if isinstance(data, dict) else None
        records: list[dict] = []
        for item in items or []:
            if not isinstance(item, dict):
                continue
            market_value = item.get("marketValue")
            amount = (
                market_value.get("amount")
                if isinstance(market_value, dict)
                else None
            )
            records.append(
                {
                    "ticker": item.get("symbol"),
                    "quantity": item.get("quantity"),
                    "market_value": amount,
                    "average_cost": item.get("averagePurchasePrice"),
                    "currency": item.get("currency"),
                    "name": item.get("name"),
                }
            )
        return records

    def fetch_cash(self, usd_krw_rate=None) -> Decimal | None:
        """Total cash in KRW from Toss buying-power (KRW + USD→KRW). None on
        failure so the caller can keep the existing baseline cash."""

        if not self.available():
            return None
        try:
            total = self._buying_power_krw("KRW")
            usd = self._buying_power_krw("USD")
        except Exception:  # noqa: BLE001 - cash read is best-effort
            return None
        if usd is not None and usd_krw_rate is not None:
            total += usd * Decimal(str(usd_krw_rate))
        return total

    def _buying_power_krw(self, currency: str) -> Decimal | None:
        data = self._client.buying_power(currency=currency)
        raw = data.get("cashBuyingPower") if isinstance(data, dict) else None
        if raw in (None, ""):
            return Decimal("0") if currency == "KRW" else None
        try:
            return Decimal(str(raw))
        except (InvalidOperation, ValueError):
            return Decimal("0") if currency == "KRW" else None

    def fetch_trades(self) -> list[dict]:
        # Trade-history sync (CLOSED order executions → journal) is Phase 14b.
        return []

    def snapshot(self) -> BrokerageSnapshot:
        return BrokerageSnapshot(
            positions=self.fetch_positions(), trades=self.fetch_trades()
        )
