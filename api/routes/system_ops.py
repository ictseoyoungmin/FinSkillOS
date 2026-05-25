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
    return (
        "OK",
        f"Sample account ready: {result.account.name}.",
        ",".join(detail_parts),
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
            "Sample events already loaded · no new rows inserted.",
            "noop_existing",
        )
    return (
        "OK",
        f"{len(created)} sample events loaded (tentative status preserved).",
        "events_seeded",
    )


__all__ = ["router"]
