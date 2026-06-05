"""Brokerage boundary tests — v3 Phase 12 / Slice 200. Read-only by contract."""

from __future__ import annotations

from finskillos.agent.ingest import proposal_from_records, trades_from_records
from finskillos.brokerage.adapter import (
    BrokerageReadAdapter,
    BrokerageSnapshot,
    NullBrokerageAdapter,
    build_brokerage_adapter,
)


def test_default_adapter_is_the_empty_null_adapter() -> None:
    adapter = build_brokerage_adapter()
    assert isinstance(adapter, NullBrokerageAdapter)
    assert adapter.available() is False
    assert adapter.fetch_positions() == []
    assert adapter.fetch_trades() == []
    assert adapter.snapshot() == BrokerageSnapshot()


def test_unknown_adapter_name_still_resolves_to_null() -> None:
    assert isinstance(build_brokerage_adapter("some_broker"), NullBrokerageAdapter)


def test_adapter_has_no_execution_method() -> None:
    # The read-only contract must never expose order/execution surface.
    adapter = build_brokerage_adapter()
    for forbidden in ("place_order", "execute", "submit_order", "buy", "sell", "trade"):
        assert not hasattr(adapter, forbidden), forbidden


def test_null_adapter_satisfies_the_read_protocol() -> None:
    assert isinstance(NullBrokerageAdapter(), BrokerageReadAdapter)


def test_a_broker_snapshot_feeds_the_existing_import_flow() -> None:
    # A future broker adapter returns records in the import shape; they flow into
    # the same confirm-gated proposals — no new write path.
    snapshot = BrokerageSnapshot(
        positions=[{"ticker": "NVDA", "quantity": 10, "market_value": 25000000}],
        trades=[{"ticker": "TSLA", "side": "long", "trade_date": "2026-06-01"}],
    )
    assert proposal_from_records(snapshot.positions).rows[0].ticker == "NVDA"
    assert trades_from_records(snapshot.trades).rows[0].ticker == "TSLA"
