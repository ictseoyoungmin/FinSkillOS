"""FastAPI app factory — Slice 13.11.

Mounts the read-only API used by the React frontend at ``/api/*``.
The app stays intentionally small: routing + CORS + a `/api/health`
probe + deterministic v4.2 Evidence-to-Judgment cockpit snapshots.
"""

from __future__ import annotations

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import (
    agent,
    analysis_workspace,
    collection_control,
    control_room,
    event_radar,
    health,
    market_kernel,
    mission_control,
    news_intelligence,
    quant_lab,
    risk_firewall,
    symbol_lab,
    system_ops,
    trade_memory,
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
        version="0.13.11",
        description=(
            "Read-only FinSkillOS adapter API for the v4.2 React "
            "Evidence-to-Judgment cockpit. "
            "Returns market state, risk interpretation, portfolio "
            "constraints, watchpoints, reflection support, and operational "
            "metadata. Mutations are limited to System Ops protocols, "
            "watchlist organization, and Trade Memory journal records. No "
            "brokerage execution or order endpoints exist."
        ),
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=_allowed_origins(),
        allow_credentials=False,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
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
    app.include_router(collection_control.router, prefix="/api")
    app.include_router(news_intelligence.router, prefix="/api")
    app.include_router(event_radar.router, prefix="/api")
    app.include_router(trade_memory.router, prefix="/api")
    app.include_router(quant_lab.router, prefix="/api")
    app.include_router(agent.router, prefix="/api")

    return app


app = create_app()


__all__ = ["app", "create_app"]
