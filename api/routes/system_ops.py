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
from datetime import date, datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends

from api.dependencies import get_session_scope, use_fixture_flag
from api.fixtures import system_ops_fixture
from api.schemas.system_ops import (
    ProtocolKey,
    ProtocolRunRecord,
    ProtocolRunResult,
    SystemOpsResponse,
)
from finskillos.data_sources import DEFAULT_US_TICKER_UNIVERSE

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
    payload.recent_protocol_runs = _read_recent_protocol_runs()
    if use_fixture:
        payload.source = "fixture"
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


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _now_iso() -> str:
    return datetime.now(tz=UTC).isoformat(timespec="seconds")


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
                ran_at=_now_iso(),
            )
            _append_protocol_run(result, db_status="LIVE", source="live")
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
                ran_at=_now_iso(),
            )
            _append_protocol_run(result, db_status="LIVE", source="live")
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
) -> None:
    try:
        path = _audit_log_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        record = ProtocolRunRecord(
            protocol=result.protocol,
            status=result.status,
            message=result.message,
            detail=result.detail,
            ran_at=result.ran_at,
            db_status=db_status,
            source=source,
        )
        with path.open("a", encoding="utf-8") as handle:
            handle.write(record.model_dump_json(by_alias=True))
            handle.write("\n")
    except OSError:
        return


def _read_recent_protocol_runs(limit: int = 5) -> list[ProtocolRunRecord]:
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

    adapter_name = os.environ.get("FINSKILLOS_MARKET_REFRESH_ADAPTER", "mock").lower()
    tickers = _with_subscribed_tickers(session, _market_refresh_tickers())
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
        f"succeeded={succeeded},failed={failed},bars={report.total_bars_written}"
    )
    if failed:
        failed_symbols = ",".join(item.ticker for item in report.failed[:5])
        detail = f"{detail},failedSymbols={failed_symbols}"
    return (status, message, detail)


def _invoke_refresh_news(session) -> tuple[str, str, str]:
    from finskillos.data_sources.adapters.rss_news_adapter import RssFeed, RssNewsAdapter
    from finskillos.db.repositories import SymbolSubscriptionRepository
    from finskillos.services.news_feed_policy import build_news_feed_policy
    from finskillos.services.news_service import NewsService

    adapter_name = os.environ.get("FINSKILLOS_NEWS_REFRESH_ADAPTER", "rss").lower()
    if adapter_name != "rss":
        return (
            "ERROR",
            "News refresh could not start. Unsupported adapter configured.",
            f"unsupported_adapter:{adapter_name}",
        )

    try:
        subscribed = SymbolSubscriptionRepository(session).active_tickers()
    except Exception:
        session.rollback()
        subscribed = ()
    policy = build_news_feed_policy(subscribed_tickers=subscribed)
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
        f"articles={len(articles)}"
    )
    return (status, message, detail)


def _invoke_calculate_indicators(session) -> tuple[str, str, str]:
    from finskillos.services.signal_service import SignalService

    tickers = _with_subscribed_tickers(session, _indicator_refresh_tickers())
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
        f"failed={len(failed)},snapshots={snapshots_written}"
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
            "Sample events already loaded · no new rows inserted.",
            "noop_existing",
        )
    return (
        "OK",
        f"{len(created)} sample events loaded (tentative status preserved).",
        "events_seeded",
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


def _with_subscribed_tickers(session, tickers: tuple[str, ...]) -> tuple[str, ...]:
    from finskillos.db.repositories import SymbolSubscriptionRepository

    try:
        subscribed = SymbolSubscriptionRepository(session).active_tickers()
    except Exception:
        session.rollback()
        subscribed = ()
    return tuple(dict.fromkeys((*tickers, *subscribed)))


__all__ = ["router"]
