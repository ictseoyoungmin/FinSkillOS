"""System Ops API — Slice 13.8.

Exposes the four read-only operational protocols the Streamlit
``finskillos.ui.pages.system_ops`` page already supports. All POST
endpoints respond with a structured ``ProtocolRunResult`` JSON — no
HTML, no raw stack traces. When the DB session is unavailable (the
default in the Slice 13.8 fixture-first shell) the protocols return
``status=NOOP`` so the React page can render a descriptive note
instead of crashing.

Safety:

* Buttons / labels use safe wording only — never "Buy" / "Sell" /
  "Execute" / "Order" / "Place Order".
* Re-running any protocol is idempotent (matches the existing
  Streamlit semantics: seed helpers skip when rows exist; risk-guard
  alerts are refreshed in place).
"""

from __future__ import annotations

import json
import os
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from fastapi import APIRouter, Depends

from api.dependencies import get_session_scope, mark_db_unavailable, use_fixture_flag
from api.fixtures import system_ops_fixture
from api.schemas.common import (
    EvidenceConflict,
    EvidenceDriver,
    EvidenceWatchpoint,
    IntegratedInterpretation,
    JudgmentHeader,
)
from api.schemas.system_ops import (
    DataSourcePill,
    ProtocolDetailEvidence,
    ProtocolKey,
    ProtocolRunRecord,
    ProtocolRunResult,
    SystemOpsResponse,
    WorkerCycleRecord,
    WorkerStatusSummary,
)
from api.timeutil import to_utc as _as_utc
from finskillos.data_sources import DEFAULT_US_TICKER_UNIVERSE
from finskillos.db.repositories import (
    SystemOpsProtocolRunRepository,
    WorkerCycleRunRepository,
)

router = APIRouter(tags=["system-ops"])

UTC = timezone.utc


@router.get(
    "/system-ops",
    response_model=SystemOpsResponse,
    summary="System Ops protocol catalogue (fixture-first in v0).",
)
def system_ops(
    use_fixture: bool = Depends(use_fixture_flag),
) -> SystemOpsResponse:
    payload = system_ops_fixture()
    if use_fixture:
        # Forced fixture stays deterministic (demos / visual baselines): keep the
        # fixture's sample run history instead of reading the local audit log.
        payload.source = "fixture"
        return payload

    with get_session_scope() as session:
        if session is None:
            # Offline: prefer real local audit runs, else show the deterministic
            # samples so the history evidence chips remain visible.
            payload.recent_protocol_runs = (
                _read_recent_protocol_runs() or payload.recent_protocol_runs
            )
            return mark_db_unavailable(payload)
        try:
            payload.recent_protocol_runs = _read_recent_protocol_runs(session=session)
            payload.worker_status = _read_worker_status(session=session)
            _attach_last_run_times(payload, session)
            payload.data_sources = _live_data_sources()
            _attach_live_evidence(payload)
            payload.source = "live"
        except Exception:
            session.rollback()
            payload.recent_protocol_runs = _read_recent_protocol_runs()
    return payload


@router.post(
    "/system-ops/seed-sample-account",
    response_model=ProtocolRunResult,
    summary="Idempotent: ensure the default account + initial snapshot exist.",
)
def run_seed_sample_account() -> ProtocolRunResult:
    return _run_protocol(
        key="seed_sample_account",
        fixture_message=(
            "Sample account protocol acknowledged. Fixture-first shell "
            "did not touch the database."
        ),
        runner=_invoke_seed_sample_account,
    )


@router.post(
    "/system-ops/refresh-market-data",
    response_model=ProtocolRunResult,
    summary="Idempotent: refresh stored market bars for the configured universe.",
)
def run_refresh_market_data() -> ProtocolRunResult:
    return _run_protocol(
        key="refresh_market_data",
        fixture_message=(
            "Market-bar refresh acknowledged. Fixture-first shell did "
            "not touch the database."
        ),
        runner=_invoke_refresh_market_data,
    )


@router.post(
    "/system-ops/refresh-news",
    response_model=ProtocolRunResult,
    summary="Idempotent: refresh stored news articles from configured feeds.",
)
def run_refresh_news() -> ProtocolRunResult:
    return _run_protocol(
        key="refresh_news",
        fixture_message=(
            "News refresh acknowledged. Fixture-first shell did not "
            "touch the database."
        ),
        runner=_invoke_refresh_news,
    )


@router.post(
    "/system-ops/calculate-indicators",
    response_model=ProtocolRunResult,
    summary="Idempotent: calculate descriptive indicators from stored bars.",
)
def run_calculate_indicators() -> ProtocolRunResult:
    return _run_protocol(
        key="calculate_indicators",
        fixture_message=(
            "Indicator calculation acknowledged. Fixture-first shell did "
            "not touch the database."
        ),
        runner=_invoke_calculate_indicators,
    )


@router.post(
    "/system-ops/recompute-regime",
    response_model=ProtocolRunResult,
    summary="Recompute the descriptive market regime over stored snapshots.",
)
def run_recompute_regime() -> ProtocolRunResult:
    return _run_protocol(
        key="recompute_regime",
        fixture_message=(
            "Regime recompute acknowledged. Fixture-first shell did not "
            "touch the database."
        ),
        runner=_invoke_recompute_regime,
    )


@router.post(
    "/system-ops/run-risk-guards",
    response_model=ProtocolRunResult,
    summary="Re-evaluate the guard ladder and refresh active alerts.",
)
def run_risk_guards() -> ProtocolRunResult:
    return _run_protocol(
        key="run_risk_guards",
        fixture_message=(
            "Risk guard refresh acknowledged. Fixture-first shell did "
            "not touch the database."
        ),
        runner=_invoke_run_risk_guards,
    )


@router.post(
    "/system-ops/seed-sample-events",
    response_model=ProtocolRunResult,
    summary="Idempotent: load the Slice-11 sample event catalog.",
)
def run_seed_sample_events() -> ProtocolRunResult:
    return _run_protocol(
        key="seed_sample_events",
        fixture_message=(
            "Sample events protocol acknowledged. Fixture-first shell "
            "did not touch the database."
        ),
        runner=_invoke_seed_sample_events,
    )


@router.post(
    "/system-ops/refresh-events",
    response_model=ProtocolRunResult,
    summary="Idempotent: ingest the event calendar from the provider adapter.",
)
def run_refresh_events() -> ProtocolRunResult:
    return _run_protocol(
        key="refresh_events",
        fixture_message=(
            "Event calendar refresh acknowledged. Fixture-first shell did "
            "not touch the database."
        ),
        runner=_invoke_refresh_events,
    )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _now_iso() -> str:
    return datetime.now(tz=UTC).isoformat(timespec="seconds")


def _live_data_sources() -> list[DataSourcePill]:
    return [
        DataSourcePill(
            label="Database",
            status="LIVE",
            detail=(
                "PostgreSQL session active; protocol and worker audit rows "
                "are DB-backed."
            ),
        ),
        DataSourcePill(
            label="Market / Indicators",
            status="LIVE",
            detail=(
                "Stored bars and indicator snapshots are read from the live DB; "
                "provider freshness is shown separately."
            ),
        ),
        DataSourcePill(
            label="News / Event Stores",
            status="LIVE",
            detail=(
                "Stored news and event metadata are read from the live DB; "
                "feed freshness depends on refresh protocols."
            ),
        ),
        DataSourcePill(
            label="Mode",
            status="LIVE",
            detail="Read mode · operational protocols only.",
        ),
    ]


def _attach_live_evidence(payload: SystemOpsResponse) -> None:
    protocol_count = str(len(payload.protocols))
    payload.judgment = JudgmentHeader(
        eyebrow="SYSTEM TRUST JUDGMENT",
        title="Local System DB-Backed",
        accent="and Ready for Read Ops",
        summary=(
            "Core protocols, audit history, worker state, and stored data "
            "summaries are reading from the live database."
        ),
        confidence=82,
    )
    payload.drivers = [
        EvidenceDriver(
            score=protocol_count,
            title="Protocols",
            note="Operational cards are available for local DB-backed workflows.",
        ),
        EvidenceDriver(
            score="Live",
            title="Data layer",
            note=(
                "Database, market snapshots, indicators, news, and event stores "
                "are reported as live DB-backed views."
            ),
        ),
        EvidenceDriver(
            score="Read",
            title="Mode",
            note="The system exposes descriptive operational protocols only.",
        ),
    ]
    payload.conflicts = [
        EvidenceConflict(
            title="Stored data vs provider freshness",
            note=(
                "Live DB rows are available; external provider freshness still "
                "depends on the refresh protocols and worker cycle."
            ),
        ),
        EvidenceConflict(
            title="Protocol actions vs trading actions",
            note="Operational buttons do not create brokerage workflows.",
        ),
    ]
    payload.interpretation = IntegratedInterpretation(
        verdict="Local System DB-Backed is the current trust read.",
        why_it_matters=(
            "The page now separates DB-backed stored views from provider "
            "freshness, so live status is easier to interpret."
        ),
        what_remains_uncertain=(
            "Freshness still depends on refresh cadence, RSS availability, "
            "and the latest worker cycle result."
        ),
    )
    payload.watchpoints = [
        EvidenceWatchpoint(
            title="Refresh cadence",
            note="Review freshness tiles before relying on stored snapshots.",
        ),
        EvidenceWatchpoint(
            title="Protocol idempotency",
            note="Read each idempotency note before running a protocol.",
        ),
        EvidenceWatchpoint(
            title="Container health",
            note="Check API and database status if protocol results drift.",
        ),
    ]


def _run_protocol(
    *,
    key: ProtocolKey,
    fixture_message: str,
    runner,  # callable(session) -> tuple[status, message, detail]
) -> ProtocolRunResult:
    """Common wrapper: open a session, call the runner, format the result.

    Errors are converted to a ``status=ERROR`` payload — the API
    contract forbids surfacing raw stack traces to the React client.
    """

    with get_session_scope() as session:
        if session is None:
            result = ProtocolRunResult(
                protocol=key,
                status="NOOP",
                message=fixture_message,
                detail="no_database_session",
                detail_evidence=_detail_evidence("no_database_session"),
                ran_at=_now_iso(),
            )
            _append_protocol_run(result, db_status="MISSING", source="fixture")
            return result
        try:
            status, message, detail = runner(session)
            session.commit()
            result = ProtocolRunResult(
                protocol=key,
                status=status,
                message=message,
                detail=detail,
                detail_evidence=_detail_evidence(detail),
                ran_at=_now_iso(),
            )
            _append_protocol_run(
                result,
                db_status="LIVE",
                source="live",
                session=session,
            )
            session.commit()
            return result
        except Exception as exc:  # noqa: BLE001 — surface as structured JSON
            session.rollback()
            result = ProtocolRunResult(
                protocol=key,
                status="ERROR",
                message=(
                    "Protocol could not complete. Stored data was not "
                    "modified."
                ),
                detail=type(exc).__name__,
                detail_evidence=_detail_evidence(type(exc).__name__),
                ran_at=_now_iso(),
            )
            _append_protocol_run(
                result,
                db_status="LIVE",
                source="live",
                session=session,
            )
            session.commit()
            return result


def _audit_log_path() -> Path:
    return Path(
        os.environ.get(
            "FINSKILLOS_SYSTEM_OPS_AUDIT_LOG",
            "data/logs/system_ops_protocol_runs.jsonl",
        )
    )


def _append_protocol_run(
    result: ProtocolRunResult,
    *,
    db_status: str,
    source: str,
    session=None,
) -> None:
    if session is not None:
        try:
            SystemOpsProtocolRunRepository(session).create(
                protocol=result.protocol,
                status=result.status,
                message=result.message,
                detail=result.detail,
                db_status=db_status,
                source=source,
                ran_at=datetime.fromisoformat(result.ran_at),
            )
        except Exception:
            session.rollback()

    try:
        path = _audit_log_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        record = ProtocolRunRecord(
            protocol=result.protocol,
            status=result.status,
            message=result.message,
            detail=result.detail,
            detail_evidence=result.detail_evidence,
            ran_at=result.ran_at,
            db_status=db_status,
            source=source,
        )
        with path.open("a", encoding="utf-8") as handle:
            handle.write(record.model_dump_json(by_alias=True))
            handle.write("\n")
    except (OSError, ValueError):
        return


def _read_recent_protocol_runs(
    limit: int = 5,
    *,
    session=None,
) -> list[ProtocolRunRecord]:
    if session is not None:
        try:
            rows = SystemOpsProtocolRunRepository(session).list_recent(limit=limit)
            return [_protocol_record_from_db(row) for row in rows]
        except Exception:
            session.rollback()

    path = _audit_log_path()
    if not path.exists():
        return []

    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return []

    records: list[ProtocolRunRecord] = []
    for line in lines[-limit:]:
        if not line.strip():
            continue
        try:
            records.append(ProtocolRunRecord.model_validate(json.loads(line)))
        except (json.JSONDecodeError, ValueError):
            continue
    return list(reversed(records))


def _attach_last_run_times(payload: SystemOpsResponse, session) -> None:
    latest = SystemOpsProtocolRunRepository(session).latest_by_protocol()
    for protocol in payload.protocols:
        row = latest.get(protocol.key)
        if row is not None:
            protocol.last_run_at = row.ran_at.isoformat()


def _protocol_record_from_db(row) -> ProtocolRunRecord:
    return ProtocolRunRecord(
        protocol=row.protocol,
        status=row.status,
        message=row.message,
        detail=row.detail,
        detail_evidence=_detail_evidence(row.detail),
        ran_at=row.ran_at.isoformat(),
        db_status=row.db_status,
        source=row.source,
    )


def _detail_evidence(detail: str) -> list[ProtocolDetailEvidence]:
    evidence: list[ProtocolDetailEvidence] = []
    for item in detail.split(","):
        chunk = item.strip()
        if not chunk:
            continue
        key, separator, value = chunk.partition("=")
        if separator:
            evidence.append(
                ProtocolDetailEvidence(key=key.strip(), value=value.strip())
            )
        else:
            evidence.append(ProtocolDetailEvidence(key="detail", value=chunk))
    return evidence


def _read_worker_status(
    limit: int = 5,
    *,
    session=None,
) -> WorkerStatusSummary:
    if session is None:
        return WorkerStatusSummary()
    try:
        rows = WorkerCycleRunRepository(session).list_recent(limit=limit)
    except Exception:
        session.rollback()
        return WorkerStatusSummary(
            latest_detail="Worker cycle history is unavailable."
        )
    if not rows:
        return WorkerStatusSummary()
    latest = rows[0]
    cadence_status, expected_next_cycle_at, cadence_detail = _worker_cadence(latest)
    return WorkerStatusSummary(
        status=_worker_status_value(latest.status),
        cadence_status=cadence_status,
        latest_started_at=latest.started_at.isoformat(),
        latest_finished_at=latest.finished_at.isoformat(),
        expected_next_cycle_at=(
            expected_next_cycle_at.isoformat() if expected_next_cycle_at else None
        ),
        latest_detail=_worker_cycle_detail(latest),
        cadence_detail=cadence_detail,
        recent_cycles=[_worker_cycle_record_from_db(row) for row in rows],
    )


def _worker_cycle_record_from_db(row) -> WorkerCycleRecord:
    return WorkerCycleRecord(
        status=_worker_status_value(row.status),
        started_at=row.started_at.isoformat(),
        finished_at=row.finished_at.isoformat(),
        timeframe=row.timeframe,
        market_status=row.market_status,
        news_status=row.news_status,
        indicator_status=row.indicator_status,
        market_scope=row.market_scope,
        news_scope=row.news_scope,
        indicator_scope=row.indicator_scope,
    )


def _worker_status_value(value: str) -> str:
    return value if value in {"OK", "NOOP", "ERROR"} else "MISSING"


def _worker_cadence(row) -> tuple[str, datetime | None, str]:
    if row.status == "ERROR":
        return (
            "ERROR",
            None,
            "Latest worker cycle ended with an error; cadence is blocked.",
        )
    if row.finished_at is None:
        return (
            "MISSING",
            None,
            "Latest worker cycle has no finish timestamp.",
        )

    finished_at = _as_utc(row.finished_at)
    interval_seconds = _worker_interval_seconds()
    grace_seconds = _worker_stale_grace_seconds(interval_seconds)
    expected_next_cycle_at = finished_at + timedelta(seconds=interval_seconds)
    stale_after = expected_next_cycle_at + timedelta(seconds=grace_seconds)
    now = datetime.now(tz=UTC)

    if now <= stale_after:
        return (
            "FRESH",
            expected_next_cycle_at,
            (
                f"On cadence; expected every {interval_seconds}s "
                f"with {grace_seconds}s grace."
            ),
        )
    lag_seconds = max(0, int((now - stale_after).total_seconds()))
    return (
        "STALE",
        expected_next_cycle_at,
        (
            f"Overdue by {lag_seconds}s after {interval_seconds}s interval "
            f"and {grace_seconds}s grace."
        ),
    )


def _worker_interval_seconds() -> int:
    return _positive_int_env("FINSKILLOS_WORKER_INTERVAL_SECONDS", 24 * 60 * 60)


def _worker_stale_grace_seconds(interval_seconds: int) -> int:
    default_grace = max(60, interval_seconds // 2)
    return _positive_int_env("FINSKILLOS_WORKER_STALE_GRACE_SECONDS", default_grace)


def _positive_int_env(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        value = int(raw)
    except ValueError:
        return default
    return max(0, value)




def _worker_cycle_detail(row) -> str:
    detail = (
        f"market={row.market_status}/{row.market_scope},"
        f"news={row.news_status}/{row.news_scope},"
        f"indicators={row.indicator_status}/{row.indicator_scope},"
        f"timeframe={row.timeframe}"
    )
    if row.status == "ERROR" and isinstance(row.summary, dict):
        error = row.summary.get("error")
        if isinstance(error, dict):
            error_type = str(error.get("type") or "WorkerError")
            detail = f"{detail},error={error_type}"
    return detail


def _invoke_seed_sample_account(session) -> tuple[str, str, str]:
    from finskillos.db.seed import seed_default_account

    result = seed_default_account(session)
    detail_parts: list[str] = []
    if result.created_account:
        detail_parts.append("account_created")
    else:
        detail_parts.append("account_reused")
    if result.created_snapshot:
        detail_parts.append("snapshot_created")
    else:
        detail_parts.append("snapshot_reused")
    if result.created_positions:
        detail_parts.append(f"positions_created={result.created_positions}")
    else:
        detail_parts.append("positions_reused")
    return (
        "OK",
        f"Sample account ready: {result.account.name}.",
        ",".join(detail_parts),
    )


def _invoke_refresh_market_data(session) -> tuple[str, str, str]:
    from finskillos.data_sources import (
        MockMarketDataAdapter,
        YahooChartMarketDataAdapter,
    )
    from finskillos.services.market_data_service import MarketDataService
    from finskillos.services.watchlist_refresh_policy import (
        build_watchlist_refresh_policy,
    )

    adapter_name = os.environ.get("FINSKILLOS_MARKET_REFRESH_ADAPTER", "yahoo").lower()
    policy = build_watchlist_refresh_policy(
        session, base_tickers=_market_refresh_tickers()
    )
    tickers = policy.tickers
    if adapter_name == "yahoo":
        adapter = YahooChartMarketDataAdapter()
    elif adapter_name == "mock":
        adapter = MockMarketDataAdapter()
    else:
        return (
            "ERROR",
            "Market-bar refresh could not start. Unsupported adapter configured.",
            f"unsupported_adapter:{adapter_name}",
        )

    service = MarketDataService(session, adapter=adapter, universe=tickers)
    report = service.refresh_bars(tickers, end=datetime.now(tz=UTC))
    failed = len(report.failed)
    succeeded = len(report.succeeded)
    status = "OK" if succeeded else "NOOP"
    message = (
        f"Market bars refreshed · adapter {adapter_name} · "
        f"{succeeded} symbols available · {report.total_bars_written} bars written."
    )
    detail = (
        f"adapter={adapter_name},tickers={len(tickers)},"
        f"succeeded={succeeded},failed={failed},bars={report.total_bars_written},"
        f"{policy.detail}"
    )
    if failed:
        failed_symbols = ",".join(item.ticker for item in report.failed[:5])
        detail = f"{detail},failedSymbols={failed_symbols}"
    return (status, message, detail)


def _invoke_refresh_news(session) -> tuple[str, str, str]:
    from finskillos.data_sources.adapters.rss_news_adapter import RssFeed, RssNewsAdapter
    from finskillos.services.news_feed_policy import build_news_feed_policy
    from finskillos.services.news_service import NewsService
    from finskillos.services.watchlist_refresh_policy import (
        build_watchlist_refresh_policy,
    )

    adapter_name = os.environ.get("FINSKILLOS_NEWS_REFRESH_ADAPTER", "rss").lower()
    if adapter_name != "rss":
        return (
            "ERROR",
            "News refresh could not start. Unsupported adapter configured.",
            f"unsupported_adapter:{adapter_name}",
        )

    watchlist_policy = build_watchlist_refresh_policy(session)
    policy = build_news_feed_policy(subscribed_tickers=watchlist_policy.tickers)
    if not policy.feeds:
        return (
            "NOOP",
            "No news feeds are available. Configure RSS feeds or ticker policy first.",
            "no_news_feeds",
        )

    adapter = RssNewsAdapter(
        tuple(
            RssFeed(url=url, source=policy.source, language=policy.language)
            for url in policy.feeds
        )
    )
    articles = tuple(adapter.fetch_latest())
    service = NewsService(session)
    for article in articles:
        service.ingest_article(article)

    status = "OK" if articles else "NOOP"
    message = (
        f"News refreshed · adapter {adapter_name} · "
        f"{len(articles)} articles ingested."
    )
    detail = (
        f"adapter={adapter_name},feeds={len(policy.feeds)},"
        f"tickers={len(policy.tickers)},generated={policy.generated},"
        f"articles={len(articles)},{watchlist_policy.detail}"
    )
    return (status, message, detail)


def _invoke_calculate_indicators(session) -> tuple[str, str, str]:
    from finskillos.services.signal_service import SignalService
    from finskillos.services.watchlist_refresh_policy import (
        build_watchlist_refresh_policy,
    )

    policy = build_watchlist_refresh_policy(
        session, base_tickers=_indicator_refresh_tickers()
    )
    tickers = policy.tickers
    service = SignalService(session)
    results = service.compute_for_universe(tickers)
    succeeded = [item for item in results if item.ok]
    failed = [item for item in results if not item.ok]
    snapshots_written = sum(item.snapshots_written for item in results)
    status = "OK" if succeeded else "NOOP"
    message = (
        f"Indicator snapshots calculated · {len(succeeded)} symbols available · "
        f"{snapshots_written} snapshots written."
    )
    detail = (
        f"tickers={len(tickers)},succeeded={len(succeeded)},"
        f"failed={len(failed)},snapshots={snapshots_written},{policy.detail}"
    )
    if failed:
        failed_symbols = ",".join(item.ticker for item in failed[:5])
        detail = f"{detail},failedSymbols={failed_symbols}"
    return (status, message, detail)


def _invoke_recompute_regime(session) -> tuple[str, str, str]:
    from finskillos.services.regime_service import RegimeService

    service = RegimeService(session)
    output = service.evaluate_today_regime(
        snapshot_time=datetime.now(tz=UTC),
        persist=True,
    )
    message = (
        f"Regime refreshed · {output.regime} · risk {output.risk_level} · "
        f"decision mode {output.decision_mode}."
    )
    return ("OK", message, output.regime)


def _invoke_run_risk_guards(session) -> tuple[str, str, str]:
    from finskillos.db.repositories import AccountRepository
    from finskillos.services.risk_guard_service import RiskGuardService

    accounts = AccountRepository(session).list_all()
    if not accounts:
        return (
            "NOOP",
            "No account is registered yet. Seed the sample account first.",
            "no_account",
        )
    target = accounts[0]
    service = RiskGuardService(session)
    report = service.evaluate(
        target.id,
        generated_at=datetime.now(tz=UTC),
        persist_alerts=True,
    )
    message = (
        f"{len(report.results)} guards re-evaluated · overall status "
        f"{report.overall_status} · risk level {report.overall_risk_level}."
    )
    return ("OK", message, report.overall_status)


def _invoke_seed_sample_events(session) -> tuple[str, str, str]:
    from finskillos.services.event_service import EventService

    created = EventService(session).seed_sample_events(today=date.today())
    if not created:
        return (
            "NOOP",
            "Event catalog already loaded · no new rows inserted.",
            "noop_existing,boundary=system_ops",
        )
    statuses = sorted({event.date_status for event in created})
    return (
        "OK",
        f"{len(created)} event catalog rows loaded through System Ops.",
        (
            f"events_seeded,created_count={len(created)},"
            f"date_statuses={'+'.join(statuses)},boundary=system_ops"
        ),
    )


def _event_calendar_adapter():
    """Select the event calendar provider, gated by
    ``FINSKILLOS_EVENT_CALENDAR_ADAPTER`` (mirrors the market-refresh adapter
    selection), without changing the protocol or read models.

    * ``mock`` (default) — offline-safe deterministic calendar.
    * ``csv`` — operator-curated calendar from ``FINSKILLOS_EVENT_CALENDAR_CSV``.
    * ``http`` — vendor JSON calendar from ``FINSKILLOS_EVENT_CALENDAR_URL``.
    """
    from finskillos.data_sources.event_adapter import (
        CsvEventCalendarAdapter,
        HttpEventCalendarAdapter,
        MockEventCalendarAdapter,
    )

    name = os.environ.get("FINSKILLOS_EVENT_CALENDAR_ADAPTER", "mock").lower()
    if name == "mock":
        return MockEventCalendarAdapter()
    if name == "csv":
        path = os.environ.get("FINSKILLOS_EVENT_CALENDAR_CSV", "").strip()
        if not path:
            raise ValueError(
                "FINSKILLOS_EVENT_CALENDAR_CSV must be set for the csv event "
                "calendar adapter"
            )
        return CsvEventCalendarAdapter(path)
    if name == "http":
        url = os.environ.get("FINSKILLOS_EVENT_CALENDAR_URL", "").strip()
        if not url:
            raise ValueError(
                "FINSKILLOS_EVENT_CALENDAR_URL must be set for the http event "
                "calendar adapter"
            )
        return HttpEventCalendarAdapter(url=url)
    raise ValueError(f"unsupported event calendar adapter: {name}")


def _invoke_refresh_events(session) -> tuple[str, str, str]:
    from finskillos.services.event_service import EventService

    adapter = _event_calendar_adapter()
    created = EventService(session).refresh_events(adapter, today=date.today())
    if not created:
        return (
            "NOOP",
            "Event calendar already current · no new rows ingested.",
            "noop_existing,boundary=system_ops",
        )
    statuses = sorted({event.date_status for event in created})
    return (
        "OK",
        f"{len(created)} calendar events ingested through System Ops.",
        (
            f"events_ingested,created_count={len(created)},"
            f"date_statuses={'+'.join(statuses)},boundary=system_ops"
        ),
    )


def _market_refresh_tickers() -> tuple[str, ...]:
    return _ticker_env("FINSKILLOS_MARKET_REFRESH_TICKERS")


def _indicator_refresh_tickers() -> tuple[str, ...]:
    return _ticker_env(
        "FINSKILLOS_INDICATOR_REFRESH_TICKERS",
        fallback=os.environ.get("FINSKILLOS_MARKET_REFRESH_TICKERS", ""),
    )


def _ticker_env(name: str, *, fallback: str = "") -> tuple[str, ...]:
    raw = os.environ.get(name, fallback)
    if not raw.strip():
        return DEFAULT_US_TICKER_UNIVERSE
    tickers = tuple(
        item.strip().upper()
        for item in raw.replace(";", ",").split(",")
        if item.strip()
    )
    return tickers or DEFAULT_US_TICKER_UNIVERSE


__all__ = ["router"]
