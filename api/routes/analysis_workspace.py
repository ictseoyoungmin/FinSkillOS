"""GET /api/analysis-workspace — Slice 13.7.

Fixture-first wrapper around ``IndexLabViewModel`` for the React
Analysis Workspace page. The route returns the same 14-ETF + 3
macro-proxy universe the Streamlit page surfaces, with deterministic
``relative_strength_score`` values + a regime-context block.

A future slice can switch the default source to live by reading
``finskillos.ui.view_models.index_lab_vm.build_index_lab_view_model``
through a session dependency; for v0 the fixture path keeps the
Playwright structural baseline stable.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from api.dependencies import use_fixture_flag
from api.fixtures import analysis_workspace_fixture
from api.schemas.analysis_workspace import AnalysisWorkspaceResponse

router = APIRouter(tags=["analysis-workspace"])


@router.get(
    "/analysis-workspace",
    response_model=AnalysisWorkspaceResponse,
    summary="Analysis Workspace / Index Lab snapshot (fixture-first in v0).",
)
def analysis_workspace(
    use_fixture: bool = Depends(use_fixture_flag),
) -> AnalysisWorkspaceResponse:
    payload = analysis_workspace_fixture()
    if use_fixture:
        payload.source = "fixture"
    return payload


__all__ = ["router"]
