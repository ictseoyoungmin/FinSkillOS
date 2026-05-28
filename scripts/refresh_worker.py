"""Run a lightweight refresh loop for local FinSkillOS operations.

The worker is intentionally simple: no Celery, no Redis, no queue. It prepares
read-model evidence by refreshing market bars, news metadata, and descriptive
indicators on a fixed interval. It never places orders or emits trade actions.
"""

from __future__ import annotations

# ruff: noqa: E402, I001

import argparse
import logging
import os
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
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
from finskillos.db.repositories import WorkerCycleRunRepository
from finskillos.db.session import session_scope
from finskillos.logging_config import setup_logging
from finskillos.services.market_data_service import MarketDataService
from finskillos.services.news_feed_policy import NewsFeedPolicy, build_news_feed_policy
from finskillos.services.signal_service import SignalService
from finskillos.services.watchlist_refresh_policy import build_watchlist_refresh_policy

logger = logging.getLogger("finskillos.scripts.refresh_worker")
UTC = timezone.utc


@dataclass(frozen=True)
class WorkerConfig:
    interval_seconds: int
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


def _bool_env(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _int_env(name: str, default: int, *, minimum: int = 1) -> int:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        value = int(raw)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer, got {raw!r}") from exc
    if value < minimum:
        raise ValueError(f"{name} must be >= {minimum}, got {value}")
    return value


def _tickers_env(name: str, default: tuple[str, ...]) -> tuple[str, ...]:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    tickers = tuple(part.strip().upper() for part in raw.split(",") if part.strip())
    return tickers or default


def load_config(args: argparse.Namespace) -> WorkerConfig:
    market_tickers = _tickers_env(
        "FINSKILLOS_MARKET_REFRESH_TICKERS", DEFAULT_US_TICKER_UNIVERSE
    )
    indicator_tickers = _tickers_env(
        "FINSKILLOS_INDICATOR_REFRESH_TICKERS", market_tickers
    )
    return WorkerConfig(
        interval_seconds=args.interval_seconds
        or _int_env("FINSKILLOS_WORKER_INTERVAL_SECONDS", 24 * 60 * 60),
        run_on_start=not args.no_run_on_start
        and _bool_env("FINSKILLOS_WORKER_RUN_ON_START", True),
        market_enabled=_bool_env("FINSKILLOS_WORKER_MARKET_ENABLED", True),
        news_enabled=_bool_env("FINSKILLOS_WORKER_NEWS_ENABLED", True),
        indicator_enabled=_bool_env("FINSKILLOS_WORKER_INDICATOR_ENABLED", True),
        market_adapter=os.getenv("FINSKILLOS_MARKET_REFRESH_ADAPTER", "mock")
        .strip()
        .lower(),
        news_adapter=os.getenv("FINSKILLOS_NEWS_REFRESH_ADAPTER", "rss")
        .strip()
        .lower(),
        news_policy=build_news_feed_policy(),
        market_tickers=market_tickers,
        indicator_tickers=indicator_tickers,
        timeframe=os.getenv("FINSKILLOS_MARKET_REFRESH_TIMEFRAME", DEFAULT_TIMEFRAME),
        persist_indicator_history=_bool_env(
            "FINSKILLOS_WORKER_PERSIST_INDICATOR_HISTORY", False
        ),
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

    with session_scope() as session:
        market_policy = build_watchlist_refresh_policy(
            session, base_tickers=config.market_tickers
        )
        indicator_policy = build_watchlist_refresh_policy(
            session, base_tickers=config.indicator_tickers
        )
        market_tickers = market_policy.tickers
        indicator_tickers = indicator_policy.tickers
        news_watchlist_policy = build_watchlist_refresh_policy(session)
        news_policy = build_news_feed_policy(
            subscribed_tickers=news_watchlist_policy.tickers
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
    return summary


def _persist_worker_cycle(session, summary: dict[str, Any]) -> None:
    market = _section_summary(summary, "market")
    news = _section_summary(summary, "news")
    indicators = _section_summary(summary, "indicators")
    WorkerCycleRunRepository(session).create(
        status=_cycle_status((market, news, indicators)),
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
    return WorkerConfig(
        interval_seconds=config.interval_seconds,
        run_on_start=config.run_on_start,
        market_enabled=config.market_enabled,
        news_enabled=config.news_enabled,
        indicator_enabled=config.indicator_enabled,
        market_adapter=config.market_adapter,
        news_adapter=config.news_adapter,
        news_policy=policy,
        market_tickers=config.market_tickers,
        indicator_tickers=config.indicator_tickers,
        timeframe=config.timeframe,
        persist_indicator_history=config.persist_indicator_history,
    )


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
            "Starting refresh worker interval=%ss run_on_start=%s "
            "market=%s news=%s indicators=%s"
        ),
        config.interval_seconds,
        config.run_on_start,
        config.market_enabled,
        config.news_enabled,
        config.indicator_enabled,
    )

    should_run_now = config.run_on_start or args.once
    try:
        while True:
            if should_run_now:
                try:
                    summary = run_cycle(config)
                    logger.info("Refresh worker cycle summary: %s", summary)
                except Exception:
                    logger.exception("Refresh worker cycle failed")
                    if args.once:
                        return 1
            if args.once:
                return 0
            should_run_now = True
            time.sleep(config.interval_seconds)
    except KeyboardInterrupt:
        logger.info("Refresh worker stopped")
        return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
