"""Run a lightweight refresh loop for local FinSkillOS operations.

The worker is intentionally simple: no Celery, no Redis, no queue. It prepares
read-model evidence by refreshing market bars and calculating descriptive
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
from finskillos.db.session import session_scope
from finskillos.logging_config import setup_logging
from finskillos.services.market_data_service import MarketDataService
from finskillos.services.signal_service import SignalService

logger = logging.getLogger("finskillos.scripts.refresh_worker")
UTC = timezone.utc


@dataclass(frozen=True)
class WorkerConfig:
    interval_seconds: int
    run_on_start: bool
    market_enabled: bool
    indicator_enabled: bool
    market_adapter: str
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
        indicator_enabled=_bool_env("FINSKILLOS_WORKER_INDICATOR_ENABLED", True),
        market_adapter=os.getenv("FINSKILLOS_MARKET_REFRESH_ADAPTER", "mock")
        .strip()
        .lower(),
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


def run_cycle(config: WorkerConfig) -> dict[str, Any]:
    """Run one refresh cycle and return a structured summary."""

    started_at = datetime.now(tz=UTC)
    summary: dict[str, Any] = {
        "startedAt": started_at.isoformat(),
        "timeframe": config.timeframe,
        "market": {"enabled": config.market_enabled, "status": "SKIPPED"},
        "indicators": {"enabled": config.indicator_enabled, "status": "SKIPPED"},
    }

    with session_scope() as session:
        if config.market_enabled:
            adapter = _build_market_adapter(config.market_adapter)
            market_service = MarketDataService(
                session, adapter=adapter, universe=config.market_tickers
            )
            report = market_service.refresh_bars(
                config.market_tickers,
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
            }

        if config.indicator_enabled:
            signal_service = SignalService(session)
            results = signal_service.compute_for_universe(
                config.indicator_tickers,
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
            }

    summary["finishedAt"] = datetime.now(tz=UTC).isoformat()
    return summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run the local FinSkillOS refresh worker. The worker refreshes "
            "market bars and descriptive indicators only."
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
        "Starting refresh worker interval=%ss run_on_start=%s market=%s indicators=%s",
        config.interval_seconds,
        config.run_on_start,
        config.market_enabled,
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
