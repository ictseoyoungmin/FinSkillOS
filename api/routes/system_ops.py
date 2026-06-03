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
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from api.dependencies import get_session_scope, mark_db_unavailable, use_fixture_flag
from api.fixtures import system_ops_fixture
from api.schemas.common import (
    EvidenceConflict,
    EvidenceDriver,
    EvidenceWatchpoint,
    IntegratedInterpretation,
    JudgmentHeader,
    SystemStatus,
)
from api.schemas.system_ops import (
    DataInvariantReport,
    DataProvenanceReport,
    DataSourcePill,
    EventCoverage,
    FeedCoverageReport,
    FeedSourceCount,
    InvariantViolation,
    NewsCoverage,
    ProtocolDetailEvidence,
    ProtocolKey,
    ProtocolRunRecord,
    ProtocolRunResult,
    ProvenanceSource,
    ProvenanceTicker,
    ProviderHealth,
    ProviderHealthTicker,
    SystemOpsResponse,
    SystemOpsRuntimeSettings,
    SystemOpsRuntimeSettingsPatch,
    WorkerCycleRecord,
    WorkerJobRow,
    WorkerLiveModeInput,
    WorkerLiveModeResult,
    WorkerStatusSummary,
)
from api.timeutil import to_utc as _as_utc
from finskillos.data_sources import DEFAULT_US_TICKER_UNIVERSE
from finskillos.db.models.system_ops import (
    WORKER_JOB_CALCULATE_INDICATORS,
    WORKER_JOB_REFRESH_MARKET,
    WORKER_JOB_REFRESH_NEWS,
)
from finskillos.db.repositories import (
    SystemOpsProtocolRunRepository,
    WorkerCycleRunRepository,
)
from finskillos.runtime_settings import (
    allowed_setting_keys,
    read_runtime_int,
    read_runtime_value,
    runtime_overlay_meta,
    runtime_setting_snapshot_for_job_queue,
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
        payload.runtime_settings = SystemOpsRuntimeSettings(**runtime_overlay_meta())
        return payload

    with get_session_scope() as session:
        if session is None:
            # Offline: prefer real local audit runs, else show the deterministic
            # samples so the history evidence chips remain visible.
            payload.recent_protocol_runs = (
                _read_recent_protocol_runs() or payload.recent_protocol_runs
            )
            payload.runtime_settings = SystemOpsRuntimeSettings(
                **runtime_overlay_meta(session=None)
            )
            return mark_db_unavailable(payload)
        try:
            payload.recent_protocol_runs = _read_recent_protocol_runs(session=session)
            payload.worker_status = _read_worker_status(session=session)
            _attach_last_run_times(payload, session)
            payload.data_sources = _live_data_sources()
            _attach_live_evidence(payload)
            payload.runtime_settings = SystemOpsRuntimeSettings(
                **runtime_overlay_meta(session=session)
            )
            payload.source = "live"
        except Exception:
            session.rollback()
            payload.recent_protocol_runs = _read_recent_protocol_runs()
            payload.runtime_settings = SystemOpsRuntimeSettings(
                **runtime_overlay_meta(session=session)
            )
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
    "/system-ops/seed-system-folder",
    response_model=ProtocolRunResult,
    summary="Idempotent: seed the protected System folder with the default universe.",
)
def run_seed_system_folder() -> ProtocolRunResult:
    return _run_protocol(
        key="seed_system_folder",
        fixture_message=(
            "System folder seed acknowledged. Fixture-first shell did not "
            "touch the database."
        ),
        runner=_invoke_seed_system_folder,
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


@router.post(
    "/system-ops/worker-live-mode",
    response_model=WorkerLiveModeResult,
    summary="Turn the worker's automatic live refresh on or off.",
)
def set_worker_live_mode(payload: WorkerLiveModeInput) -> WorkerLiveModeResult:
    with get_session_scope() as session:
        if session is None:
            return WorkerLiveModeResult(
                live_mode=payload.live_mode,
                message="No database session is reachable; worker live mode is unchanged.",
            )
        try:
            from finskillos.db.repositories import WorkerControlRepository

            row = WorkerControlRepository(session).set_live_mode(
                payload.live_mode, updated_by="system_ops"
            )
            session.commit()
            return WorkerLiveModeResult(
                live_mode=row.live_mode,
                message=(
                    "Worker live mode ON — automatic refresh resumes on the next cycle."
                    if row.live_mode
                    else "Worker live mode OFF — automatic refresh paused. Manual "
                    "refresh protocols still work."
                ),
                updated_at=row.updated_at.isoformat(),
            )
        except Exception as exc:  # noqa: BLE001 — structured JSON, never a raw stack
            session.rollback()
            return WorkerLiveModeResult(
                live_mode=payload.live_mode,
                message=(
                    "Worker live mode could not be updated "
                    f"({type(exc).__name__}). Stored state is unchanged."
                ),
            )


@router.post(
    "/system-ops/worker-jobs/{job_id}/retry",
    response_model=WorkerStatusSummary,
    summary="Re-enqueue a finished worker job to recover a failed (or re-run a "
    "done) refresh.",
)
def retry_worker_job(job_id: UUID) -> WorkerStatusSummary:
    with get_session_scope() as session:
        if session is None:
            return WorkerStatusSummary()
        from finskillos.db.repositories import WorkerJobRepository

        repo = WorkerJobRepository(session)
        job = repo.get(job_id)
        if job is None:
            raise HTTPException(status_code=404, detail="job_not_found")
        if job.status not in _JOB_TERMINAL:
            # Still QUEUED/RUNNING — nothing to recover; avoid duplicate work.
            raise HTTPException(status_code=409, detail="job_not_terminal")

        payload = job.payload if isinstance(job.payload, dict) else {}
        folder_id = payload.get("folder_id")
        new_payload: dict[str, Any] = {
            "requested_from": "worker_job_retry",
            "runtime_settings": runtime_setting_snapshot_for_job_queue(session=session),
        }
        dedup = job.job_type
        if folder_id:
            new_payload["folder_id"] = folder_id
            dedup = f"{job.job_type}:folder={folder_id}"
        repo.enqueue(
            job.job_type,
            requested_by="worker_job_retry",
            dedup_key=dedup,
            payload=new_payload,
        )
        session.commit()
        return _read_worker_status(session=session)


@router.get(
    "/system-ops/runtime-settings",
    response_model=SystemOpsRuntimeSettings,
    summary="Read effective runtime settings for ops tab.",
)
def get_system_ops_runtime_settings(
    use_fixture: bool = Depends(use_fixture_flag),
) -> SystemOpsRuntimeSettings:
    if use_fixture:
        # Keep fixture mode deterministic and avoid opening a session just to
        # read overrides; live values are shown in fixture mode anyway.
        return SystemOpsRuntimeSettings(**runtime_overlay_meta(session=None))

    with get_session_scope() as session:
        if session is None:
            return SystemOpsRuntimeSettings(**runtime_overlay_meta(session=None))
        return SystemOpsRuntimeSettings(**runtime_overlay_meta(session=session))


@router.patch(
    "/system-ops/runtime-settings",
    response_model=SystemOpsRuntimeSettings,
    summary="Persist runtime settings overrides from Operations tab.",
)
def update_system_ops_runtime_settings(
    payload: SystemOpsRuntimeSettingsPatch,
    use_fixture: bool = Depends(use_fixture_flag),
) -> SystemOpsRuntimeSettings:
    if use_fixture:
        # Fixture mode does not block writes in the browser, but there is no durable
        # row there to persist into. Return what the user typed so the UI remains
        # consistent with the request body.
        data = runtime_overlay_meta(session=None)
        normalized = _normalize_runtime_settings_payload(payload.values)
        if normalized:
            data["values"].update(normalized)
            data["overrides"].update(normalized)
            data["captured_at"] = datetime.now(tz=UTC).isoformat(timespec="seconds")
        return SystemOpsRuntimeSettings(**data)

    with get_session_scope() as session:
        if session is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database unavailable; settings changes require DB availability.",
            )

        normalized = _normalize_runtime_settings_payload(payload.values)
        if normalized:
            from finskillos.db.repositories import SystemOpsSettingsRepository

            SystemOpsSettingsRepository(session).patch(
                normalized, updated_by="system_ops_api"
            )
            session.commit()
        return SystemOpsRuntimeSettings(**runtime_overlay_meta(session=session))


_SYNTHETIC_SOURCES = {"mock", "test"}


@router.get(
    "/system-ops/feed-coverage",
    response_model=FeedCoverageReport,
    summary="News + event feed coverage diagnostics (counts, freshness, sources).",
)
def feed_coverage() -> FeedCoverageReport:
    with get_session_scope() as session:
        if session is None:
            return FeedCoverageReport(
                generated_at=_now_iso(),
                system_status=SystemStatus(db="UNAVAILABLE", mode="READ_MODE"),
                source="fixture",
                detail="Database unavailable; feed coverage cannot be read.",
            )
        from finskillos.db.repositories import (
            EventRepository,
            NewsArticleRepository,
        )

        now = datetime.now(tz=UTC)
        news_repo = NewsArticleRepository(session)
        latest_news = news_repo.latest_published_at()
        total_articles = news_repo.count()
        if total_articles == 0:
            news_freshness = "EMPTY"
        elif latest_news and (now - _as_utc(latest_news)).days <= 3:
            news_freshness = "FRESH"
        else:
            news_freshness = "STALE"
        news = NewsCoverage(
            total_articles=total_articles,
            latest_published_at=latest_news.isoformat() if latest_news else None,
            recent_articles=news_repo.count_since(now - timedelta(days=7)),
            freshness_status=news_freshness,
            sources=_feed_source_counts(news_repo.source_counts()),
        )

        event_repo = EventRepository(session)
        latest_event = event_repo.latest_start_date()
        events = EventCoverage(
            total_events=event_repo.count(),
            upcoming_events=event_repo.count_upcoming(today=now.date()),
            latest_event_date=latest_event.isoformat() if latest_event else None,
            sources=_feed_source_counts(event_repo.source_counts()),
            date_status=_feed_source_counts(event_repo.date_status_counts()),
        )

        detail = (
            f"News: {news.total_articles} stored ({news.freshness_status.lower()}, "
            f"{news.recent_articles} in 7d). Events: {events.total_events} stored, "
            f"{events.upcoming_events} upcoming."
        )
        return FeedCoverageReport(
            generated_at=_now_iso(),
            system_status=SystemStatus(db="LIVE", mode="READ_MODE"),
            source="live",
            news=news,
            events=events,
            detail=detail,
        )


def _feed_source_counts(counts: dict[str, int]) -> list[FeedSourceCount]:
    return [
        FeedSourceCount(source=src, count=count)
        for src, count in sorted(counts.items(), key=lambda item: item[1], reverse=True)
    ]


@router.get(
    "/system-ops/data-invariants",
    response_model=DataInvariantReport,
    summary="Audit stored-data invariants (e.g. every indicator snapshot has a "
    "backing market bar).",
)
def data_invariants() -> DataInvariantReport:
    with get_session_scope() as session:
        if session is None:
            return DataInvariantReport(
                generated_at=_now_iso(),
                system_status=SystemStatus(db="UNAVAILABLE", mode="READ_MODE"),
                source="fixture",
                detail="Database unavailable; invariants cannot be checked.",
            )
        from finskillos.db.repositories import IndicatorRepository

        repo = IndicatorRepository(session)
        total = repo.count_total()
        orphans = repo.count_orphan_snapshots()
        samples = (
            [
                InvariantViolation(
                    ticker=ticker, timeframe=timeframe, at=snapshot_time.isoformat()
                )
                for ticker, timeframe, snapshot_time in repo.list_orphan_snapshots()
            ]
            if orphans
            else []
        )
        if orphans == 0:
            status = "OK"
            detail = (
                f"All {total} indicator snapshot(s) have a backing market bar."
                if total
                else "No indicator snapshots are stored yet."
            )
        else:
            status = "VIOLATIONS"
            names = ", ".join(sorted({v.ticker for v in samples})[:8])
            detail = (
                f"{orphans} of {total} indicator snapshot(s) have no backing market "
                f"bar ({names}) — they can surface phantom indicator values."
            )
        return DataInvariantReport(
            generated_at=_now_iso(),
            system_status=SystemStatus(db="LIVE", mode="READ_MODE"),
            source="live",
            status=status,
            total_snapshots=total,
            orphan_snapshot_count=orphans,
            orphan_samples=samples,
            detail=detail,
        )


@router.get(
    "/system-ops/data-provenance",
    response_model=DataProvenanceReport,
    summary="Where the stored market bars came from (source distribution + "
    "synthetic-source tickers).",
)
def data_provenance() -> DataProvenanceReport:
    with get_session_scope() as session:
        if session is None:
            return DataProvenanceReport(
                generated_at=_now_iso(),
                system_status=SystemStatus(db="UNAVAILABLE", mode="READ_MODE"),
                source="fixture",
                detail="Database unavailable; provenance cannot be read.",
            )
        from finskillos.db.repositories import MarketRepository

        repo = MarketRepository(session)
        distribution = repo.source_distribution()
        latest = repo.latest_source_by_ticker()

        total = sum(distribution.values())
        real = sum(
            count
            for src, count in distribution.items()
            if src not in _SYNTHETIC_SOURCES
        )
        sources = [
            ProvenanceSource(
                source=src, bar_count=count, synthetic=src in _SYNTHETIC_SOURCES
            )
            for src, count in sorted(
                distribution.items(), key=lambda item: item[1], reverse=True
            )
        ]
        synthetic_tickers = [
            ProvenanceTicker(
                ticker=ticker,
                source=src,
                latest_at=bar_time.isoformat() if bar_time else None,
            )
            for ticker, (src, bar_time) in sorted(latest.items())
            if src in _SYNTHETIC_SOURCES
        ]
        ratio = round(real / total * 100) if total else 0
        if total == 0:
            detail = "No market bars are stored yet."
        elif synthetic_tickers:
            names = ", ".join(t.ticker for t in synthetic_tickers[:8])
            detail = (
                f"{ratio}% of bars are real; {len(synthetic_tickers)} ticker(s) "
                f"still show a synthetic latest bar ({names}) — refresh them with the "
                "real adapter."
            )
        else:
            detail = f"All {total} stored bars are from real sources ({ratio}%)."

        return DataProvenanceReport(
            generated_at=_now_iso(),
            system_status=SystemStatus(db="LIVE", mode="READ_MODE"),
            source="live",
            total_bars=total,
            real_bars=real,
            real_ratio_percent=ratio,
            distinct_tickers=len(latest),
            sources=sources,
            synthetic_tickers=synthetic_tickers,
            detail=detail,
        )


@router.post(
    "/system-ops/runtime-settings/reset",
    response_model=SystemOpsRuntimeSettings,
    summary="Revert every runtime override back to its .env default.",
)
def reset_system_ops_runtime_settings() -> SystemOpsRuntimeSettings:
    with get_session_scope() as session:
        if session is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database unavailable; settings changes require DB availability.",
            )
        from finskillos.db.repositories import SystemOpsSettingsRepository

        repo = SystemOpsSettingsRepository(session)
        current = dict(repo.get().values or {})
        if current:
            # Patch each overridden key to None → reverts to .env, recorded in history.
            repo.patch(
                {key: None for key in current}, updated_by="system_ops_reset"
            )
            session.commit()
        return SystemOpsRuntimeSettings(**runtime_overlay_meta(session=session))


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
    live_mode = _read_worker_live_mode(session)
    job_counts, recent_jobs = _read_worker_jobs(session)
    provider_health = _provider_health(session)
    try:
        rows = WorkerCycleRunRepository(session).list_recent(limit=limit)
    except Exception:
        session.rollback()
        return WorkerStatusSummary(
            live_mode=live_mode,
            latest_detail="Worker cycle history is unavailable.",
            job_counts=job_counts,
            recent_jobs=recent_jobs,
            provider_health=provider_health,
        )
    if not rows:
        return WorkerStatusSummary(
            live_mode=live_mode,
            job_counts=job_counts,
            recent_jobs=recent_jobs,
            provider_health=provider_health,
        )
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
        live_mode=live_mode,
        recent_cycles=[_worker_cycle_record_from_db(row) for row in rows],
        job_counts=job_counts,
        recent_jobs=recent_jobs,
        provider_health=provider_health,
    )


def _provider_health(session) -> ProviderHealth:
    """Roll up market-provider health from recent worker cycles.

    Scans the recent cycle audit for the latest success (bars written), the latest
    failure (failed tickers or an errored cycle), how many newest cycles in a row
    had failures, and which tickers failed most recently — so an operator can see
    *why* coverage is partial, not just that it is."""
    try:
        rows = WorkerCycleRunRepository(session).list_recent(limit=25)
    except Exception:
        session.rollback()
        return ProviderHealth()
    market_rows = [(row, _market_section(row)) for row in rows]
    market_rows = [(row, m) for row, m in market_rows if m.get("enabled")]
    if not market_rows:
        return ProviderHealth(status="UNKNOWN")

    latest_row, latest_market = market_rows[0]
    adapter = str(latest_market.get("adapter") or "")

    # Last fully-clean cycle (collected bars with zero failures) — the clearest
    # "the provider last worked completely at X" signal.
    last_success_at = next(
        (
            row.finished_at.isoformat()
            for row, m in market_rows
            if int(m.get("barsWritten") or 0) > 0 and int(m.get("failed") or 0) == 0
        ),
        None,
    )
    last_failure_at = next(
        (
            row.finished_at.isoformat()
            for row, m in market_rows
            if int(m.get("failed") or 0) > 0 or row.status == "ERROR"
        ),
        None,
    )

    consecutive = 0
    for row, m in market_rows:
        if int(m.get("failed") or 0) > 0 or row.status == "ERROR":
            consecutive += 1
        else:
            break

    affected = next(
        (m.get("failedTickers") for _row, m in market_rows if m.get("failedTickers")),
        None,
    )
    affected_tickers = [
        ProviderHealthTicker(
            ticker=str(item.get("ticker") or ""),
            error=str(item.get("error") or ""),
        )
        for item in (affected or [])
        if isinstance(item, dict)
    ]

    latest_failed = int(latest_market.get("failed") or 0)
    if consecutive == 0:
        status = "HEALTHY"
    elif latest_failed > 0 and int(latest_market.get("succeeded") or 0) > 0:
        status = "DEGRADED"  # partial: some tickers failing
    else:
        status = "FAILING"

    return ProviderHealth(
        adapter=adapter,
        status=status,
        last_cycle_at=latest_row.finished_at.isoformat(),
        last_success_at=last_success_at,
        last_failure_at=last_failure_at,
        consecutive_failure_cycles=consecutive,
        affected_tickers=affected_tickers,
        detail=_provider_health_detail(adapter, status, affected_tickers),
    )


def _market_section(row) -> dict:
    summary = row.summary if isinstance(row.summary, dict) else {}
    section = summary.get("market")
    return section if isinstance(section, dict) else {}


def _provider_health_detail(adapter, status, affected) -> str:
    label = adapter or "market provider"
    if status == "HEALTHY":
        return f"{label}: healthy — the latest cycle collected without failures."
    if status == "UNKNOWN":
        return f"{label}: no market cycle has run yet."
    names = ", ".join(t.ticker for t in affected[:8]) if affected else "some tickers"
    if status == "DEGRADED":
        return f"{label}: degraded — partial coverage; {names} failed most recently."
    return f"{label}: failing — recent cycles collected no bars ({names})."


_JOB_TERMINAL = {"DONE", "ERROR"}


def _read_worker_jobs(session) -> tuple[dict[str, int], list[WorkerJobRow]]:
    from finskillos.db.repositories import WorkerJobRepository

    try:
        repo = WorkerJobRepository(session)
        counts = repo.count_by_status()
        rows = repo.list_recent(limit=10)
    except Exception:
        session.rollback()
        return {}, []
    return counts, [_worker_job_row(job) for job in rows]


def _worker_job_row(job) -> WorkerJobRow:
    payload = job.payload if isinstance(job.payload, dict) else {}
    folder_id = payload.get("folder_id") if isinstance(payload, dict) else None
    error = job.error
    if error and len(error) > 200:
        error = error[:197] + "…"
    return WorkerJobRow(
        id=str(job.id),
        job_type=job.job_type,
        status=job.status,
        requested_by=job.requested_by,
        folder_id=str(folder_id) if folder_id else None,
        created_at=job.created_at.isoformat() if job.created_at else None,
        finished_at=job.finished_at.isoformat() if job.finished_at else None,
        error=error,
        retryable=job.status in _JOB_TERMINAL,
    )


def _read_worker_live_mode(session) -> bool:
    from finskillos.db.repositories import WorkerControlRepository

    try:
        return WorkerControlRepository(session).is_live_mode()
    except Exception:
        session.rollback()
        return True


def _worker_cycle_record_from_db(row) -> WorkerCycleRecord:
    counts = _worker_cycle_counts(row.summary)
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
        bars_written=counts["bars_written"],
        articles_ingested=counts["articles_ingested"],
        snapshots_written=counts["snapshots_written"],
        failures=counts["failures"],
        regime=counts["regime"],
        outcome=_worker_cycle_outcome(row, counts),
    )


def _worker_cycle_counts(summary) -> dict:
    """Pull the per-component results out of the cycle summary JSONB."""
    s = summary if isinstance(summary, dict) else {}

    def _section(name: str) -> dict:
        value = s.get(name)
        return value if isinstance(value, dict) else {}

    market, news, indicators, regime = (
        _section("market"),
        _section("news"),
        _section("indicators"),
        _section("regime"),
    )

    def _int(block: dict, key: str) -> int:
        try:
            return int(block.get(key) or 0)
        except (TypeError, ValueError):
            return 0

    return {
        "bars_written": _int(market, "barsWritten"),
        "articles_ingested": _int(news, "articlesIngested"),
        "snapshots_written": _int(indicators, "snapshotsWritten"),
        "failures": _int(market, "failed") + _int(indicators, "failed"),
        "regime": str(regime.get("regime")) if regime.get("regime") else None,
    }


def _worker_cycle_outcome(row, counts: dict) -> str:
    """A human-readable one-line summary of what the cycle did."""
    if row.status == "ERROR":
        detail = ""
        if isinstance(row.summary, dict):
            error = row.summary.get("error")
            if isinstance(error, dict):
                detail = f" ({error.get('type') or 'WorkerError'})"
        return f"Cycle failed{detail} — no data was written; the next cycle retries."
    parts: list[str] = []
    if row.market_status not in {"SKIPPED", "MISSING"}:
        parts.append(f"{counts['bars_written']} bars")
    if row.news_status not in {"SKIPPED", "MISSING"}:
        parts.append(f"{counts['articles_ingested']} articles")
    if row.indicator_status not in {"SKIPPED", "MISSING"}:
        parts.append(f"{counts['snapshots_written']} indicator snapshots")
    if counts["regime"]:
        parts.append(f"regime {counts['regime']}")
    if not parts:
        return "Nothing collected this cycle (all sections skipped)."
    line = "Collected " + ", ".join(parts) + "."
    if counts["failures"]:
        line += f" {counts['failures']} ticker(s) failed and stay partial."
    return line


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
    return read_runtime_int(
        "FINSKILLOS_WORKER_INTERVAL_SECONDS", default=24 * 60 * 60
    )


def _worker_stale_grace_seconds(interval_seconds: int) -> int:
    default_grace = max(60, interval_seconds // 2)
    return read_runtime_int("FINSKILLOS_WORKER_STALE_GRACE_SECONDS", default=default_grace)


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


def _invoke_seed_system_folder(session) -> tuple[str, str, str]:
    from finskillos.db.seed import seed_system_folder

    result = seed_system_folder(session)
    detail_parts = [
        "folder_created" if result.created_folder else "folder_reused",
        f"subscribed={result.subscribed}",
        f"linked={result.linked}",
        f"members={result.members}",
    ]
    message = (
        f"System folder ready · {result.members} sector leaders tracked "
        f"({result.linked} newly linked)."
    )
    return ("OK", message, ",".join(detail_parts))


def _invoke_refresh_market_data(session) -> tuple[str, str, str]:
    return _enqueue_refresh_job(session, WORKER_JOB_REFRESH_MARKET, "Market-bar refresh")


def _invoke_refresh_news(session) -> tuple[str, str, str]:
    return _enqueue_refresh_job(session, WORKER_JOB_REFRESH_NEWS, "News refresh")


def _invoke_calculate_indicators(session) -> tuple[str, str, str]:
    return _enqueue_refresh_job(
        session, WORKER_JOB_CALCULATE_INDICATORS, "Indicator calculation"
    )


def _enqueue_refresh_job(session, job_type: str, label: str) -> tuple[str, str, str]:
    """Queue a worker job instead of running the refresh synchronously.

    The worker (request-driven via the Postgres queue, Slice 113) claims and
    runs the job, so the API returns immediately and never blocks on a provider
    call. Enqueue is idempotent on the job type, so repeated clicks while a job
    is still pending never duplicate work (the same queued job is returned)."""
    from finskillos.db.repositories import WorkerJobRepository

    job = WorkerJobRepository(session).enqueue(
        job_type,
        requested_by="system_ops",
        dedup_key=job_type,
        payload={
            "requested_from": "system_ops",
            "runtime_settings": runtime_setting_snapshot_for_job_queue(session=session),
        },
    )
    return (
        "QUEUED",
        (
            f"{label} queued for the worker. The dashboard refreshes once the "
            "worker completes the job."
        ),
        f"job_queued,job_type={job_type},job_id={job.id},boundary=system_ops",
    )


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


def _normalize_runtime_settings_payload(
    raw: dict[str, Any] | None,
) -> dict[str, Any]:
    normalized: dict[str, Any] = {}
    if not isinstance(raw, dict):
        return normalized

    allowed = set(allowed_setting_keys())
    for key, value in raw.items():
        if not isinstance(key, str):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid runtime setting key: {key!r}",
            )
        if key not in allowed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported runtime setting key: {key!r}",
            )
        if value is None:
            normalized[key] = None
        elif isinstance(value, (str, int, bool)):
            normalized[key] = str(value)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Unsupported runtime setting value type for {key!r}: "
                    f"{type(value).__name__}"
                ),
            )
    return normalized


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
    raw = read_runtime_value(
        "FINSKILLOS_MARKET_REFRESH_TICKERS",
        default=",".join(DEFAULT_US_TICKER_UNIVERSE),
    )
    if raw is None:
        return DEFAULT_US_TICKER_UNIVERSE
    tickers = tuple(
        part.strip().upper()
        for part in raw.replace(";", ",").split(",")
        if part.strip()
    )
    return tickers or DEFAULT_US_TICKER_UNIVERSE


def _indicator_refresh_tickers() -> tuple[str, ...]:
    fallback = read_runtime_value(
        "FINSKILLOS_MARKET_REFRESH_TICKERS",
        default=",".join(DEFAULT_US_TICKER_UNIVERSE),
    )
    raw = read_runtime_value(
        "FINSKILLOS_INDICATOR_REFRESH_TICKERS", default=fallback
    )
    if raw is None:
        return _normalize_tickers(fallback)
    tickers = tuple(
        part.strip().upper()
        for part in raw.replace(";", ",").split(",")
        if part.strip()
    )
    return tickers or _normalize_tickers(fallback)


def _normalize_tickers(raw: str) -> tuple[str, ...]:
    return tuple(
        part.strip().upper()
        for part in raw.replace(";", ",").split(",")
        if part.strip()
    ) or DEFAULT_US_TICKER_UNIVERSE


__all__ = ["router"]
