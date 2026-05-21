"""FastAPI app factory — Slice 13.6.

Mounts the read-only API used by the React frontend at ``/api/*``.
The app is intentionally tiny: routing + CORS + a `/api/health`
probe + the Control Room route. Every other product route is
deferred to future slices but the placeholder is reserved so the
React shell can render a clear "coming soon" state without 404.
"""

from __future__ import annotations

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import (
    analysis_workspace,
    control_room,
    health,
    market_kernel,
    mission_control,
    risk_firewall,
    symbol_lab,
    system_ops,
)


def _allowed_origins() -> list[str]:
    """Return the CORS allow-list for the React frontend.

    Defaults match the Vite dev server (5173) and the nginx-served
    production container (3000). Override via the
    ``FINSKILLOS_CORS_ORIGINS`` env var as a comma-separated list.
    """

    raw = os.environ.get(
        "FINSKILLOS_CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000",
    )
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


def create_app() -> FastAPI:
    app = FastAPI(
        title="FinSkillOS API",
        version="0.13.8",
        description=(
            "Read-only FinSkillOS adapter API for the v4.1 React cockpit. "
            "Returns market state, risk interpretation, portfolio "
            "constraints, watchpoints, and reflection support. The only "
            "writes exposed are the System Ops operational protocols "
            "(seed sample data, recompute regime, run risk guards). No "
            "execution / order / trade endpoints exist."
        ),
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=_allowed_origins(),
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )

    app.include_router(health.router, prefix="/api")
    app.include_router(control_room.router, prefix="/api")
    app.include_router(market_kernel.router, prefix="/api")
    app.include_router(analysis_workspace.router, prefix="/api")
    app.include_router(symbol_lab.router, prefix="/api")
    app.include_router(risk_firewall.router, prefix="/api")
    app.include_router(mission_control.router, prefix="/api")
    app.include_router(system_ops.router, prefix="/api")

    return app


app = create_app()


__all__ = ["app", "create_app"]
