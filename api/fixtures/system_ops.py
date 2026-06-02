"""System Ops fixture — Slice 13.8.

Deterministic payload for ``GET /api/system-ops``. Mirrors the v4.1
mockup ``page-ops`` section: data-layer pills + four operational
protocol cards. Wording is safe by contract — no execution / order /
buy / sell phrasing appears anywhere.
"""

from __future__ import annotations

from api.fixtures._common import FIXTURE_TIMESTAMP
from api.fixtures._v42 import conflicts, drivers, interpretation, judgment, watchpoints
from api.schemas.common import SystemStatus
from api.schemas.system_ops import (
    DataSourcePill,
    ProtocolCard,
    ProtocolDetailEvidence,
    ProtocolRunRecord,
    SystemOpsResponse,
)


def sample_protocol_runs() -> list[ProtocolRunRecord]:
    """Deterministic recent-run history so the System Ops history evidence chips
    are visible in fixture/visual mode even with an empty local audit log.

    These are demo records (``source="fixture"``); a live or populated-audit
    response replaces them with real ``ProtocolRunRecord`` rows.
    """
    return [
        ProtocolRunRecord(
            protocol="calculate_indicators",
            status="OK",
            message="Descriptive indicator snapshots computed from stored bars.",
            detail="snapshots=12, tickers=12",
            detail_evidence=[
                ProtocolDetailEvidence(key="snapshots", value="12"),
                ProtocolDetailEvidence(key="tickers", value="12"),
            ],
            ran_at="2026-05-20T11:40:00+09:00",
            db_status="LIVE",
            source="fixture",
        ),
        ProtocolRunRecord(
            protocol="refresh_market_data",
            status="OK",
            message="Stored OHLCV bars refreshed for the focus universe.",
            detail="bars=120, tickers=12",
            detail_evidence=[
                ProtocolDetailEvidence(key="bars", value="120"),
                ProtocolDetailEvidence(key="tickers", value="12"),
            ],
            ran_at="2026-05-20T11:20:00+09:00",
            db_status="LIVE",
            source="fixture",
        ),
        ProtocolRunRecord(
            protocol="seed_sample_events",
            status="NOOP",
            message="Event catalog already present; no new rows seeded.",
            detail="noop_existing, boundary=system_ops",
            detail_evidence=[
                ProtocolDetailEvidence(key="detail", value="noop_existing"),
                ProtocolDetailEvidence(key="boundary", value="system_ops"),
            ],
            ran_at="2026-05-20T10:55:00+09:00",
            db_status="LIVE",
            source="fixture",
        ),
    ]


def system_ops_fixture() -> SystemOpsResponse:
    return SystemOpsResponse(
        generated_at=FIXTURE_TIMESTAMP,
        source="fixture",
        recent_protocol_runs=sample_protocol_runs(),
        system_status=SystemStatus(db="LIVE", mode="READ_MODE", guard_count=3),
        judgment=judgment(
            "SYSTEM TRUST JUDGMENT",
            "Local System Usable",
            "with Partial Data",
            (
                "Core protocols are available in read mode while several "
                "data sources remain fixture-first."
            ),
            69,
        ),
        drivers=drivers(
            (
                "6",
                "Protocols",
                "Operational cards are available for deterministic local workflows.",
            ),
            ("Fixture", "Data layer", "Market, event, and news stores remain fixture-first."),
            ("Read", "Mode", "The system exposes operational protocols only."),
        ),
        conflicts=conflicts(
            (
                "Usable system vs fixture data",
                "The cockpit can run locally, but source freshness is limited.",
            ),
            (
                "Protocol actions vs trading actions",
                "Operational buttons do not create brokerage workflows.",
            ),
        ),
        interpretation=interpretation(
            "Local System Usable with Partial Data is the current trust read.",
            "The page explains data-source status and safe operational protocols before a run.",
            "Live adapter state and last-run timestamps can change the confidence level.",
        ),
        watchpoints=watchpoints(
            ("Fixture source", "Review data-source pills before relying on freshness."),
            ("Protocol idempotency", "Read each idempotency note before running a protocol."),
            ("Container health", "Check API and database status if protocol results drift."),
        ),
        protocols=[
            ProtocolCard(
                key="seed_sample_account",
                title="Seed sample account",
                description=(
                    "Creates the default Main Trading Account and an "
                    "initial portfolio snapshot used by the cockpit."
                ),
                idempotency_note=(
                    "Idempotent · reuses the existing account and snapshot when already present."
                ),
                button_label="Seed sample data",
                confirm_label="Seed sample data",
                tone="info",
                last_run_at=None,
            ),
            ProtocolCard(
                key="seed_system_folder",
                title="Seed system folder",
                description=(
                    "Registers the protected System folder with the install-default "
                    "sector leaders so collection runs out of the box. Operators add "
                    "their own folders and tickers from the Collection Control surface."
                ),
                idempotency_note=(
                    "Idempotent · the folder, subscriptions, and memberships are "
                    "upserted; operator-adjusted collection flags are preserved."
                ),
                button_label="Seed system folder",
                confirm_label="Seed system folder",
                tone="info",
                last_run_at=None,
            ),
            ProtocolCard(
                key="refresh_market_data",
                title="Refresh market bars",
                description=(
                    "Updates stored OHLCV bars for the configured focus universe. "
                    "Product pages remain read-only snapshots."
                ),
                idempotency_note=(
                    "Idempotent · existing bars are upserted by ticker, timeframe, "
                    "and timestamp."
                ),
                button_label="Refresh stored bars",
                confirm_label="Refresh stored bars",
                tone="success",
                last_run_at=None,
            ),
            ProtocolCard(
                key="refresh_news",
                title="Refresh news feeds",
                description=(
                    "Reads configured RSS or Atom feeds and stores article "
                    "metadata plus short summaries for News Intelligence."
                ),
                idempotency_note=(
                    "Idempotent · existing articles are upserted by URL; "
                    "full article bodies are not stored."
                ),
                button_label="Refresh news metadata",
                confirm_label="Refresh news metadata",
                tone="info",
                last_run_at=None,
            ),
            ProtocolCard(
                key="calculate_indicators",
                title="Calculate indicators",
                description=(
                    "Computes descriptive technical snapshots from stored bars. "
                    "No provider request is made during this protocol."
                ),
                idempotency_note=(
                    "Idempotent · latest snapshots are upserted by ticker, "
                    "timeframe, and snapshot time."
                ),
                button_label="Calculate indicators",
                confirm_label="Calculate indicators",
                tone="info",
                last_run_at=None,
            ),
            ProtocolCard(
                key="recompute_regime",
                title="Recompute market regime",
                description=(
                    "Re-runs the regime interpretation pipeline over the "
                    "stored indicator snapshots. Descriptive only."
                ),
                idempotency_note=(
                    "Idempotent · the latest stored regime is updated "
                    "in place; no historical rows are removed."
                ),
                button_label="Recompute interpretation",
                confirm_label="Recompute interpretation",
                tone="info",
                last_run_at=None,
            ),
            ProtocolCard(
                key="run_risk_guards",
                title="Run risk guards",
                description=(
                    "Re-evaluates the full guard ladder for the default "
                    "account and refreshes the active alerts table."
                ),
                idempotency_note=(
                    "Idempotent · same-day alerts are refreshed in place "
                    "instead of stacking new rows."
                ),
                button_label="Refresh stored view",
                confirm_label="Run protocol",
                tone="warning",
                last_run_at=None,
            ),
            ProtocolCard(
                key="seed_sample_events",
                title="Seed event catalog",
                description=(
                    "Loads the deterministic Slice-11 event catalog through "
                    "the System Ops ingestion boundary. Catalyst Watch stays "
                    "read-only."
                ),
                idempotency_note=(
                    "Idempotent · existing rows are skipped by title; "
                    "date statuses remain TENTATIVE / SPECULATIVE / WINDOW."
                ),
                button_label="Seed event catalog",
                confirm_label="Seed event catalog",
                tone="info",
                last_run_at=None,
            ),
            ProtocolCard(
                key="refresh_events",
                title="Refresh event calendar",
                description=(
                    "Ingests the event calendar from the provider adapter "
                    "(offline-safe mock by default) through the System Ops "
                    "ingestion boundary. Catalyst Watch stays read-only."
                ),
                idempotency_note=(
                    "Idempotent · existing rows are skipped by title; ingested "
                    "rows keep uncertain TENTATIVE / WINDOW date statuses."
                ),
                button_label="Refresh event calendar",
                confirm_label="Refresh event calendar",
                tone="info",
                last_run_at=None,
            ),
        ],
        data_sources=[
            DataSourcePill(
                label="Database",
                status="FIXTURE",
                detail="Fixture-first in Slice 13.8 · live DB optional.",
            ),
            DataSourcePill(
                label="Market / Indicators",
                status="FIXTURE",
                detail="Stored bar refresh and indicator calculation are available.",
            ),
            DataSourcePill(
                label="News / Event Stores",
                status="FIXTURE",
                detail="RSS refresh and System Ops event ingestion protocols available.",
            ),
            DataSourcePill(
                label="Mode",
                status="LIVE",
                detail="Read mode · operational protocols only.",
            ),
        ],
        runtime_settings={
            "values": {
                "FINSKILLOS_WORKER_INTERVAL_SECONDS": "86400",
                "FINSKILLOS_WORKER_POLL_SECONDS": "5",
                "FINSKILLOS_WORKER_STALE_GRACE_SECONDS": "43200",
                "FINSKILLOS_WORKER_RUN_ON_START": "1",
                "FINSKILLOS_WORKER_MARKET_ENABLED": "1",
                "FINSKILLOS_WORKER_NEWS_ENABLED": "1",
                "FINSKILLOS_WORKER_INDICATOR_ENABLED": "1",
                "FINSKILLOS_WORKER_PERSIST_INDICATOR_HISTORY": "0",
                "FINSKILLOS_MARKET_REFRESH_ADAPTER": "yahoo",
                "FINSKILLOS_MARKET_REFRESH_TICKERS": (
                    "SPY,QQQ,NVDA,TSLA,AAPL,MSFT,AMZN,SMH,SOXX,VIX,US10Y,DXY"
                ),
                "FINSKILLOS_INDICATOR_REFRESH_TICKERS": (
                    "SPY,QQQ,NVDA,TSLA,AAPL,MSFT,AMZN,SMH,SOXX,VIX,US10Y,DXY"
                ),
                "FINSKILLOS_MARKET_REFRESH_TIMEFRAME": "1d",
                "FINSKILLOS_REFRESH_FOLDER_NAMES": "",
                "FINSKILLOS_NEWS_REFRESH_ADAPTER": "rss",
                "FINSKILLOS_NEWS_RSS_FEEDS": "",
                "FINSKILLOS_NEWS_RSS_TICKERS": "AAPL,MSFT,NVDA,TSLA",
                "FINSKILLOS_NEWS_RSS_SOURCE": "",
                "FINSKILLOS_NEWS_RSS_LANGUAGE": "en-US",
            },
            "overrides": {},
            "capturedAt": FIXTURE_TIMESTAMP,
        },
    )


__all__ = ["system_ops_fixture"]
