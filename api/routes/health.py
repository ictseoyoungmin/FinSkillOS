"""GET /api/health — readiness probe for the React shell."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter

from api.schemas.common import CamelModel

router = APIRouter(tags=["health"])


class HealthResponse(CamelModel):
    status: str
    service: str
    mode: str
    generated_at: datetime


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        service="finskillos-api",
        mode="READ_MODE",
        generated_at=datetime.now(tz=timezone.utc),
    )


__all__ = ["router"]
