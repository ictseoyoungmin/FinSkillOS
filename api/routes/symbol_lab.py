"""GET /api/symbol-lab — Slice 13.7.

Fixture-first wrapper around ``SymbolLabViewModel`` for the React
Symbol Lab page. Returns the technical snapshot + recent bars +
position context + alerts + news for a single ticker. A future slice
can wire the live path through ``build_symbol_lab_view_model``; for
v0 the fixture keeps the Playwright baseline deterministic.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from api.dependencies import use_fixture_flag
from api.fixtures import symbol_lab_fixture
from api.schemas.symbol_lab import SymbolLabResponse

router = APIRouter(tags=["symbol-lab"])


@router.get(
    "/symbol-lab",
    response_model=SymbolLabResponse,
    summary="Symbol Lab snapshot for a single ticker (fixture-first in v0).",
)
def symbol_lab(
    ticker: str | None = Query(
        default=None,
        description=(
            "Uppercased ticker (NVDA / TSLA / AAPL / MSFT / SMH). Defaults "
            "to TSLA when omitted. Unknown tickers return a MISSING-status "
            "payload with a setup hint."
        ),
    ),
    use_fixture: bool = Depends(use_fixture_flag),
) -> SymbolLabResponse:
    payload = symbol_lab_fixture(ticker)
    if use_fixture:
        payload.source = "fixture"
    return payload


__all__ = ["router"]
