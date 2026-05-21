"""System Ops fixture — Slice 13.8.

Deterministic payload for ``GET /api/system-ops``. Mirrors the v4.1
mockup ``page-ops`` section: data-layer pills + four operational
protocol cards. Wording is safe by contract — no execution / order /
buy / sell phrasing appears anywhere.
"""

from __future__ import annotations

from api.fixtures._common import FIXTURE_TIMESTAMP
from api.schemas.common import SystemStatus
from api.schemas.system_ops import (
    DataSourcePill,
    ProtocolCard,
    SystemOpsResponse,
)


def system_ops_fixture() -> SystemOpsResponse:
    return SystemOpsResponse(
        generated_at=FIXTURE_TIMESTAMP,
        source="fixture",
        system_status=SystemStatus(db="LIVE", mode="READ_MODE", guard_count=3),
        protocols=[
            ProtocolCard(
                key="seed_sample_account",
                title="Seed sample account",
                description=(
                    "Creates the default Main Trading Account and an "
                    "initial portfolio snapshot used by the cockpit."
                ),
                idempotency_note=(
                    "Idempotent · reuses the existing account and "
                    "snapshot when already present."
                ),
                button_label="Seed sample data",
                confirm_label="Seed sample data",
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
                title="Seed sample events",
                description=(
                    "Loads the deterministic Slice-11 catalog of "
                    "uncertain events. Status remains tentative / "
                    "speculative / window."
                ),
                idempotency_note=(
                    "Idempotent · existing rows are skipped by title; "
                    "no event is upgraded to CONFIRMED automatically."
                ),
                button_label="Seed sample data",
                confirm_label="Seed sample data",
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
                label="Market Bars",
                status="FIXTURE",
                detail="Stored data only · no automatic live refresh.",
            ),
            DataSourcePill(
                label="News / Event Stores",
                status="FIXTURE",
                detail="Manual upsert and seed helpers available.",
            ),
            DataSourcePill(
                label="Mode",
                status="LIVE",
                detail="Read mode · operational protocols only.",
            ),
        ],
    )


__all__ = ["system_ops_fixture"]
