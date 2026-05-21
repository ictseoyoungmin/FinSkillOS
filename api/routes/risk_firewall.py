"""GET /api/risk-firewall — Slice 13.8.

Fixture-first wrapper around the Slice-06 RiskGuardReport view. The
route stays fixture-first so the React shell + Playwright visual
baseline remain deterministic; live DB wiring is deferred per the
dependencies.py TODO note.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from api.dependencies import use_fixture_flag
from api.fixtures import risk_firewall_fixture
from api.schemas.risk_firewall import RiskFirewallResponse

router = APIRouter(tags=["risk-firewall"])


@router.get(
    "/risk-firewall",
    response_model=RiskFirewallResponse,
    summary="Risk Firewall snapshot (fixture-first in v0).",
)
def risk_firewall(
    use_fixture: bool = Depends(use_fixture_flag),
) -> RiskFirewallResponse:
    payload = risk_firewall_fixture()
    if use_fixture:
        payload.source = "fixture"
    return payload


__all__ = ["router"]
