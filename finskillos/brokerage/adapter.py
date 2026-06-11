"""Brokerage read-only adapter boundary — v3 Phase 12 / Slice 200.

The deliberate, minimal extension point for "추후 증권 API". A brokerage may only
**read** — fetch positions / trades — and feed them into the *same* Phase-9 import
flow (``proposal_from_records`` / ``trades_from_records`` → preview → confirm). So
a broker is just another descriptive-bookkeeping source: no new write power.

There is **no order / execution method on this protocol by design.** Execution is
out of scope and stays a separate, later, conservative, paper-first, default-off,
explicitly-authorized decision (the user: "거래는 하지 않을 것이며 하더라도 가장
마지막에 보수적인 계약으로"). No real adapter ships yet — the default is the empty
``NullBrokerageAdapter``.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

__all__ = [
    "BrokerageSnapshot",
    "BrokerageReadAdapter",
    "NullBrokerageAdapter",
    "build_brokerage_adapter",
    "EXECUTION_BOUNDARY",
]

EXECUTION_BOUNDARY = (
    "Read-only by contract. A brokerage adapter may import positions and trades "
    "into the existing confirm-gated bookkeeping import; it cannot place orders "
    "or execute trades. Execution, if ever added, is a separate, conservative, "
    "paper-first, default-off, explicitly-authorized contract."
)


@dataclass(frozen=True)
class BrokerageSnapshot:
    """Read-only broker data, in the record shape the import tools accept."""

    positions: list[dict] = field(default_factory=list)
    trades: list[dict] = field(default_factory=list)


@runtime_checkable
class BrokerageReadAdapter(Protocol):
    """A read-only brokerage source. Intentionally has no execution method."""

    name: str

    def available(self) -> bool: ...

    def fetch_positions(self) -> list[dict]: ...

    def fetch_trades(self) -> list[dict]: ...

    def snapshot(self) -> BrokerageSnapshot: ...


class NullBrokerageAdapter:
    """Default no-op adapter — no broker configured, returns nothing."""

    name = "null"

    def available(self) -> bool:
        return False

    def fetch_positions(self) -> list[dict]:
        return []

    def fetch_trades(self) -> list[dict]:
        return []

    def snapshot(self) -> BrokerageSnapshot:
        return BrokerageSnapshot()


def build_brokerage_adapter(name: str | None = None) -> BrokerageReadAdapter:
    """Resolve the configured brokerage adapter (env
    ``FINSKILLOS_BROKERAGE_ADAPTER``; default ``null``).

    ``toss`` resolves to the read-only Toss adapter (v4); anything else (incl. the
    default) is the empty ``NullBrokerageAdapter``. Every adapter feeds the existing
    confirm-gated import flow and none gains execution power.
    """

    resolved = (
        name or os.getenv("FINSKILLOS_BROKERAGE_ADAPTER", "null")
    ).strip().lower()
    if resolved == "toss":
        from finskillos.brokerage.toss.adapter import TossBrokerageAdapter

        return TossBrokerageAdapter()
    return NullBrokerageAdapter()
