"""GET /api/control-room — first React page payload.

Slice 13.6 ships the fixture path. The route is wired so a future
slice can switch to live DB by reading the existing
``ControlRoomViewModel`` builder, but the default response stays
fixture-first to keep the v4.1 cockpit visual baseline deterministic
for Playwright.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from api.dependencies import use_fixture_flag
from api.fixtures import control_room_fixture
from api.schemas.control_room import ControlRoomResponse

router = APIRouter(tags=["control-room"])


@router.get(
    "/control-room",
    response_model=ControlRoomResponse,
    summary="Control Room snapshot (fixture-first in v0).",
)
def control_room(
    use_fixture: bool = Depends(use_fixture_flag),
) -> ControlRoomResponse:
    """Return the Control Room read model for the React shell.

    ``use_fixture`` is currently informational — even when ``False``
    we still return the deterministic fixture. A future slice will
    delegate to :func:`finskillos.ui.view_models.build_control_room_view_model`
    when the DB is wired and the schema mapper is in place.
    """

    payload = control_room_fixture()
    if use_fixture:
        payload.source = "fixture"
    return payload


@router.get(
    "/mock/control-room",
    response_model=ControlRoomResponse,
    include_in_schema=False,
)
def control_room_mock() -> ControlRoomResponse:
    """Always returns the fixture, no matter what the client sends.

    Useful for Playwright screenshots that want to guarantee a stable
    payload even if a future slice flips the default of
    ``/control-room`` to live DB.
    """

    return control_room_fixture()


__all__ = ["router"]
