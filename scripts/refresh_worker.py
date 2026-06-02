"""Run a lightweight refresh loop for local FinSkillOS operations.

The worker is intentionally simple: no Celery, no Redis, no queue. It prepares
read-model evidence by refreshing market bars, news metadata, and descriptive
indicators on a fixed interval. It never places orders or emits trade actions.
"""

from __future__ import annotations

# ruff: noqa: E402, I001

import argparse
import dataclasses
import logging
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from collections.abc import Mapping
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from finskillos.config import get_settings
from finskillos.data_sources import (
    DEFAULT_TIMEFRAME,
    DEFAULT_US_TICKER_UNIVERSE,
    MockMarketDataAdapter,
    YahooChartMarketDataAdapter,
)
from finskillos.db.models.system_ops import (
    WORKER_JOB_CALCULATE_INDICATORS,
    WORKER_JOB_REFRESH_ALL,
    WORKER_JOB_REFRESH_MARKET,
    WORKER_JOB_REFRESH_NEWS,
)
from finskillos.db.repositories import (
    WorkerControlRepository,
    WorkerCycleRunRepository,
    WorkerJobRepository,
)
from finskillos.db.session import session_scope
from finskillos.logging_config import setup_logging
from finskillos.services.market_data_service import MarketDataService
from finskillos.services.news_feed_policy import NewsFeedPolicy, build_news_feed_policy
from finskillos.services.signal_service import SignalService
from finskillos.services.watchlist_refresh_policy import build_watchlist_refresh_policy
from finskillos.runtime_settings import (
    read_runtime_bool,
    read_runtime_csv,
    read_runtime_int,
    read_runtime_value,
)

logger = logging.getLogger("finskillos.scripts.refresh_worker")
UTC = timezone.utc


class WorkerCycleFailed(RuntimeError):
    """Raised after a failed worker cycle has been recorded."""

    def __init__(self, summary: dict[str, Any]) -> None:
        super().__init__("refresh worker cycle failed")
        self.summary = summary


@dataclass(frozen=True)
class WorkerConfig:
    interval_seconds: int
    poll_seconds: int
    run_on_start: bool
    market_enabled: bool
    news_enabled: bool
    indicator_enabled: bool
    market_adapter: str
    news_adapter: str
    news_policy: NewsFeedPolicy
    market_tickers: tuple[str, ...]
    indicator_tickers: tuple[str, ...]
    timeframe: str
    persist_indicator_history: bool
    runtime_overrides: Mapping[str, str] | None = None


def _resolve_tickers(
    name: str,
    *,
    fallback: tuple[str, ...],
    runtime_overrides: Mapping[str, str] | None,
) -> tuple[str, ...]:
    values = read_runtime_csv(name, runtime_overrides=runtime_overrides)
    if not values:
        return fallback
    return tuple(value.upper() for value in values)


def load_config(
    args: argparse.Namespace,
    *,
    runtime_overrides: Mapping[str, str] | None = None,
) -> WorkerConfig:
    market_tickers = _resolve_tickers(
        "FINSKILLOS_MARKET_REFRESH_TICKERS",
        fallback=DEFAULT_US_TICKER_UNIVERSE,
        runtime_overrides=runtime_overrides,
    )
    indicator_tickers = _resolve_tickers(
        "FINSKILLOS_INDICATOR_REFRESH_TICKERS",
        fallback=market_tickers,
        runtime_overrides=runtime_overrides,
    )
    timeframe = read_runtime_value(
        "FINSKILLOS_MARKET_REFRESH_TIMEFRAME",
        default=DEFAULT_TIMEFRAME,
        runtime_overrides=runtime_overrides,
    )
    return WorkerConfig(
        interval_seconds=args.interval_seconds
        or read_runtime_int(
            "FINSKILLOS_WORKER_INTERVAL_SECONDS",
            default=24 * 60 * 60,
            runtime_overrides=runtime_overrides,
        ),
        poll_seconds=read_runtime_int(
            "FINSKILLOS_WORKER_POLL_SECONDS",
            default=5,
            runtime_overrides=runtime_overrides,
        ),
        run_on_start=not args.no_run_on_start
        and read_runtime_bool(
            "FINSKILLOS_WORKER_RUN_ON_START",
            default=True,
            runtime_overrides=runtime_overrides,
        ),
        market_enabled=read_runtime_bool(
            "FINSKILLOS_WORKER_MARKET_ENABLED",
            default=True,
            runtime_overrides=runtime_overrides,
        ),
        news_enabled=read_runtime_bool(
            "FINSKILLOS_WORKER_NEWS_ENABLED",
            default=True,
            runtime_overrides=runtime_overrides,
        ),
        indicator_enabled=read_runtime_bool(
            "FINSKILLOS_WORKER_INDICATOR_ENABLED",
            default=True,
            runtime_overrides=runtime_overrides,
        ),
        market_adapter=read_runtime_value(
            "FINSKILLOS_MARKET_REFRESH_ADAPTER",
            default="yahoo",
            runtime_overrides=runtime_overrides,
        ).strip()
        .lower(),
        news_adapter=read_runtime_value(
            "FINSKILLOS_NEWS_REFRESH_ADAPTER",
            default="rss",
            runtime_overrides=runtime_overrides,
        ).strip()
        .lower(),
        news_policy=build_news_feed_policy(),
        market_tickers=market_tickers,
        indicator_tickers=indicator_tickers,
        timeframe=timeframe,
        persist_indicator_history=read_runtime_bool(
            "FINSKILLOS_WORKER_PERSIST_INDICATOR_HISTORY",
            default=False,
            runtime_overrides=runtime_overrides,
        ),
        runtime_overrides=runtime_overrides,
    )


def _build_market_adapter(adapter_name: str):
    if adapter_name == "mock":
        return MockMarketDataAdapter()
    if adapter_name == "yahoo":
        return YahooChartMarketDataAdapter()
    raise ValueError(
        "FINSKILLOS_MARKET_REFRESH_ADAPTER must be one of: mock, yahoo"
    )


def _build_news_adapter(config: WorkerConfig):
    if config.news_adapter != "rss":
        raise ValueError("FINSKILLOS_NEWS_REFRESH_ADAPTER must be one of: rss")
    from finskillos.data_sources.adapters.rss_news_adapter import RssFeed, RssNewsAdapter

    return RssNewsAdapter(
        tuple(
            RssFeed(
                url=url,
                source=config.news_policy.source,
                language=config.news_policy.language,
            )
            for url in config.news_policy.feeds
        )
    )


def run_cycle(config: WorkerConfig) -> dict[str, Any]:
    """Run one refresh cycle and return a structured summary."""

    started_at = datetime.now(tz=UTC)
    summary: dict[str, Any] = {
        "startedAt": started_at.isoformat(),
        "timeframe": config.timeframe,
        "market": {"enabled": config.market_enabled, "status": "SKIPPED"},
        "news": {"enabled": config.news_enabled, "status": "SKIPPED"},
        "indicators": {"enabled": config.indicator_enabled, "status": "SKIPPED"},
    }

    try:
        with session_scope() as session:
            market_policy = build_watchlist_refresh_policy(
                session,
                base_tickers=config.market_tickers,
                collection_type="market",
                runtime_overrides=config.runtime_overrides,
            )
            indicator_policy = build_watchlist_refresh_policy(
                session,
                base_tickers=config.indicator_tickers,
                collection_type="indicator",
                runtime_overrides=config.runtime_overrides,
            )
            market_tickers = market_policy.tickers
            indicator_tickers = indicator_policy.tickers
            news_watchlist_policy = build_watchlist_refresh_policy(
                session,
                collection_type="news",
                runtime_overrides=config.runtime_overrides,
            )
            news_policy = build_news_feed_policy(
                subscribed_tickers=news_watchlist_policy.tickers,
                runtime_overrides=config.runtime_overrides,
            )
            config = _with_news_policy(config, news_policy)
            if config.market_enabled:
                adapter = _build_market_adapter(config.market_adapter)
                market_service = MarketDataService(
                    session, adapter=adapter, universe=market_tickers
                )
                report = market_service.refresh_bars(
                    market_tickers,
                    timeframe=config.timeframe,
                    end=datetime.now(tz=UTC),
                )
                summary["market"] = {
                    "enabled": True,
                    "status": "OK" if report.succeeded else "NOOP",
                    "adapter": config.market_adapter,
                    "tickers": len(report.results),
                    "succeeded": len(report.succeeded),
                    "failed": len(report.failed),
                    "barsWritten": report.total_bars_written,
                    "scope": market_policy.scope,
                    "folders": market_policy.folder_names,
                }

            if config.news_enabled:
                if not config.news_policy.feeds:
                    summary["news"] = {
                        "enabled": True,
                        "status": "NOOP",
                        "adapter": config.news_adapter,
                        "feeds": 0,
                        "tickers": 0,
                        "generated": config.news_policy.generated,
                        "articlesIngested": 0,
                        "scope": news_watchlist_policy.scope,
                        "folders": news_watchlist_policy.folder_names,
                    }
                else:
                    from finskillos.services.news_service import NewsService

                    adapter = _build_news_adapter(config)
                    articles = tuple(adapter.fetch_latest())
                    news_service = NewsService(session)
                    for article in articles:
                        news_service.ingest_article(article)
                    summary["news"] = {
                        "enabled": True,
                        "status": "OK" if articles else "NOOP",
                        "adapter": config.news_adapter,
                        "feeds": len(config.news_policy.feeds),
                        "tickers": len(config.news_policy.tickers),
                        "generated": config.news_policy.generated,
                        "articlesIngested": len(articles),
                        "scope": news_watchlist_policy.scope,
                        "folders": news_watchlist_policy.folder_names,
                    }

            if config.indicator_enabled:
                signal_service = SignalService(session)
                results = signal_service.compute_for_universe(
                    indicator_tickers,
                    timeframe=config.timeframe,
                    persist_history=config.persist_indicator_history,
                )
                succeeded = [item for item in results if item.ok]
                failed = [item for item in results if not item.ok]
                summary["indicators"] = {
                    "enabled": True,
                    "status": "OK" if succeeded else "NOOP",
                    "tickers": len(results),
                    "succeeded": len(succeeded),
                    "failed": len(failed),
                    "snapshotsWritten": sum(item.snapshots_written for item in results),
                    "scope": indicator_policy.scope,
                    "folders": indicator_policy.folder_names,
                }

            summary["finishedAt"] = datetime.now(tz=UTC).isoformat()
            _persist_worker_cycle(session, summary)
    except Exception as exc:
        _record_failed_worker_cycle(summary, exc)
        raise WorkerCycleFailed(summary) from exc
    return summary


def _persist_worker_cycle(session, summary: dict[str, Any]) -> None:
    market = _section_summary(summary, "market")
    news = _section_summary(summary, "news")
    indicators = _section_summary(summary, "indicators")
    WorkerCycleRunRepository(session).create(
        status=str(summary.get("status") or _cycle_status((market, news, indicators))),
        started_at=datetime.fromisoformat(str(summary["startedAt"])),
        finished_at=datetime.fromisoformat(str(summary["finishedAt"])),
        timeframe=str(summary.get("timeframe") or DEFAULT_TIMEFRAME),
        market_status=str(market.get("status") or "SKIPPED"),
        news_status=str(news.get("status") or "SKIPPED"),
        indicator_status=str(indicators.get("status") or "SKIPPED"),
        market_scope=str(market.get("scope") or "unknown"),
        news_scope=str(news.get("scope") or "unknown"),
        indicator_scope=str(indicators.get("scope") or "unknown"),
        summary=summary,
    )


def _record_failed_worker_cycle(summary: dict[str, Any], exc: Exception) -> None:
    summary["status"] = "ERROR"
    summary["finishedAt"] = datetime.now(tz=UTC).isoformat()
    summary["error"] = {
        "type": exc.__class__.__name__,
        "message": str(exc),
    }
    try:
        with session_scope() as session:
            _persist_worker_cycle(session, summary)
    except Exception:
        logger.exception("Failed to persist refresh worker error summary")


def _section_summary(summary: dict[str, Any], key: str) -> dict[str, Any]:
    value = summary.get(key)
    return value if isinstance(value, dict) else {"status": "SKIPPED"}


def _cycle_status(sections: tuple[dict[str, Any], ...]) -> str:
    statuses = [str(section.get("status") or "SKIPPED") for section in sections]
    if "ERROR" in statuses:
        return "ERROR"
    if "OK" in statuses:
        return "OK"
    return "NOOP"


def _with_news_policy(config: WorkerConfig, policy: NewsFeedPolicy) -> WorkerConfig:
    return dataclasses.replace(config, news_policy=policy)


# Job queue (Slice 113) -------------------------------------------------------

_JOB_ENABLES: dict[str, dict[str, bool]] = {
    WORKER_JOB_REFRESH_MARKET: {
        "market_enabled": True,
        "news_enabled": False,
        "indicator_enabled": False,
    },
    WORKER_JOB_REFRESH_NEWS: {
        "market_enabled": False,
        "news_enabled": True,
        "indicator_enabled": False,
    },
    WORKER_JOB_CALCULATE_INDICATORS: {
        "market_enabled": False,
        "news_enabled": False,
        "indicator_enabled": True,
    },
}


def _config_for_job(config: WorkerConfig, job_type: str) -> WorkerConfig:
    """A config variant enabling only the refresh(es) a job needs."""
    if job_type == WORKER_JOB_REFRESH_ALL:
        return config
    overrides = _JOB_ENABLES.get(job_type)
    if overrides is None:
        raise ValueError(f"unknown worker job type: {job_type}")
    return dataclasses.replace(config, **overrides)


def enqueue_refresh(
    job_type: str = WORKER_JOB_REFRESH_ALL,
    *,
    requested_by: str = "worker",
) -> None:
    """Idempotently queue a refresh job (dedup on its own type)."""
    with session_scope() as session:
        WorkerJobRepository(session).enqueue(
            job_type, requested_by=requested_by, dedup_key=job_type
        )


def live_mode_enabled() -> bool:
    """Whether the cockpit has the worker's automatic refresh turned on.

    Read each cycle so the toggle takes effect without a restart. Defaults to
    ``True`` if the control row can't be read (fail toward staying fresh)."""
    try:
        with session_scope() as session:
            return WorkerControlRepository(session).is_live_mode()
    except Exception:
        logger.exception("Could not read worker live mode; assuming ON")
        return True


def drain_queue(config: WorkerConfig, *, max_jobs: int = 50) -> int:
    """Claim and process queued jobs until the queue is empty (or the cap)."""
    processed = 0
    while processed < max_jobs:
        with session_scope() as session:
            job = WorkerJobRepository(session).claim_next()
            if job is None:
                return processed
            job_id, job_type = job.id, job.job_type
        summary: dict[str, Any] | None = None
        error: str | None = None
        try:
            runtime_overrides = _extract_runtime_settings_from_job_payload(
                job_payload=job_payload(job)
            )
            effective_config = config
            if runtime_overrides is not None:
                effective_config = load_config(
                    argparse.Namespace(
                        interval_seconds=config.interval_seconds,
                        no_run_on_start=False,
                    ),
                    runtime_overrides=runtime_overrides,
                )
            summary = run_cycle(_config_for_job(effective_config, job_type))
        except WorkerCycleFailed as exc:
            summary = exc.summary
            error = str(exc.summary.get("error", {}).get("message") or "cycle failed")
        except Exception as exc:  # noqa: BLE001 — recorded on the job row
            error = f"{exc.__class__.__name__}: {exc}"
        with session_scope() as session:
            repo = WorkerJobRepository(session)
            job = repo.get(job_id)
            if job is not None:
                if error is None:
                    repo.complete(job, summary)
                else:
                    if summary is not None:
                        job.result = summary
                    repo.fail(job, error)
        logger.info(
            "Worker job %s (%s) -> %s", job_id, job_type, "ERROR" if error else "DONE"
        )
        processed += 1
    return processed


def _coerce_runtime_overrides(payload: Mapping[str, str] | None) -> dict[str, str] | None:
    if not payload:
        return None
    output: dict[str, str] = {}
    for key, value in payload.items():
        if isinstance(value, str):
            output[key] = value
    return output or None


def _extract_runtime_settings_from_job_payload(
    job_payload: dict[str, object] | None,
) -> dict[str, str] | None:
    if not isinstance(job_payload, dict):
        return None

    raw = job_payload.get("runtime_settings")
    if not isinstance(raw, dict):
        return None
    return _coerce_runtime_overrides({
        key: str(value)
        for key, value in raw.items()
        if isinstance(key, str) and isinstance(value, (str, int, bool))
    })


def job_payload(job) -> dict[str, object] | None:
    payload = getattr(job, "payload", None)
    if payload is None:
        return None
    if isinstance(payload, dict):
        return payload
    return None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run the local FinSkillOS refresh worker. The worker refreshes "
            "market bars, news metadata, and descriptive indicators."
        )
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run one refresh cycle and exit.",
    )
    parser.add_argument(
        "--interval-seconds",
        type=int,
        default=None,
        help="Override FINSKILLOS_WORKER_INTERVAL_SECONDS.",
    )
    parser.add_argument(
        "--no-run-on-start",
        action="store_true",
        help="Sleep for the first interval before running the first cycle.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    settings = get_settings()
    setup_logging(settings.log_level)
    config = load_config(args)

    logger.info(
        (
            "Starting refresh worker interval=%ss poll=%ss run_on_start=%s "
            "market=%s news=%s indicators=%s"
        ),
        config.interval_seconds,
        config.poll_seconds,
        config.run_on_start,
        config.market_enabled,
        config.news_enabled,
        config.indicator_enabled,
    )

    # `--once` runs one full cycle directly (the original behaviour, used by the
    # operations tests). The daemon is queue-driven: it idles, processes any
    # queued jobs each poll tick, and enqueues a periodic refresh on the
    # interval (and on start). `enqueue` is dedup-safe, so the periodic job
    # never piles up behind a still-running one.
    if args.once:
        try:
            summary = run_cycle(config)
            logger.info("Refresh worker cycle summary: %s", summary)
            return 0
        except Exception:
            logger.exception("Refresh worker cycle failed")
            return 1

    try:
        if config.run_on_start and live_mode_enabled():
            enqueue_refresh(requested_by="worker_start")
        next_interval = time.monotonic() + config.interval_seconds
        while True:
            # Manual jobs (System Ops refresh buttons) are always processed;
            # only the automatic enqueue honours the cockpit live-mode toggle.
            try:
                drain_queue(config)
            except Exception:
                logger.exception("Worker queue drain failed")
            if time.monotonic() >= next_interval:
                try:
                    if live_mode_enabled():
                        enqueue_refresh(requested_by="worker_interval")
                    else:
                        logger.info("Worker live mode OFF — skipping interval refresh")
                except Exception:
                    logger.exception("Worker interval enqueue failed")
                next_interval = time.monotonic() + config.interval_seconds
            time.sleep(config.poll_seconds)
    except KeyboardInterrupt:
        logger.info("Refresh worker stopped")
        return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
