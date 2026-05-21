"""GET /api/mission-control — Slice 13.8.

Fixture-first wrapper around the Slice-03 GoalService + Slice-03
PortfolioService read models. Fixture-first per dependencies.py TODO.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from api.dependencies import use_fixture_flag
from api.fixtures import mission_control_fixture
from api.schemas.mission_control import MissionControlResponse

router = APIRouter(tags=["mission-control"])


@router.get(
    "/mission-control",
    response_model=MissionControlResponse,
    summary="Mission Control snapshot (fixture-first in v0).",
)
def mission_control(
    use_fixture: bool = Depends(use_fixture_flag),
) -> MissionControlResponse:
    payload = mission_control_fixture()
    if use_fixture:
        payload.source = "fixture"
    return payload


__all__ = ["router"]
