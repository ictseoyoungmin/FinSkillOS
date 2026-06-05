"""Scheduled report generation tests — Slice 174.

Exercises the daily / weekly report builders and the generate_report.py script
against an on-disk SQLite database.
"""

from __future__ import annotations

import os
import subprocess
from datetime import date
from decimal import Decimal
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from api.weekly_report import build_report_markdown
from finskillos.db.base import Base
from finskillos.db.repositories import AccountRepository
from finskillos.services.event_service import (
    EventInput,
    EventLinkInput,
    EventService,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
_FORBIDDEN = ("buy now", "sell now", "지금 사라", "지금 팔아라")


def _seed(db_url: str) -> None:
    engine = create_engine(db_url, future=True)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    with factory() as session:
        AccountRepository(session).create(
            name="Main Trading Account", target_value=Decimal("100000000")
        )
        session.commit()
    engine.dispose()


def test_daily_brief_omits_trade_review(tmp_path: Path) -> None:
    db_url = f"sqlite+pysqlite:///{tmp_path / 'r.db'}"
    _seed(db_url)
    engine = create_engine(db_url, future=True)
    with sessionmaker(bind=engine)() as session:
        md = build_report_markdown(session, period="daily", today=date(2026, 6, 5))
    engine.dispose()
    assert md.startswith("# Daily Brief")
    assert "## Market Regime" in md
    assert "## Portfolio" in md
    assert "## Upcoming Catalysts" in md
    assert "## Trade Process Review" not in md
    for forbidden in _FORBIDDEN:
        assert forbidden not in md.lower()


def test_weekly_report_includes_trade_review(tmp_path: Path) -> None:
    db_url = f"sqlite+pysqlite:///{tmp_path / 'r.db'}"
    _seed(db_url)
    engine = create_engine(db_url, future=True)
    with sessionmaker(bind=engine)() as session:
        md = build_report_markdown(session, period="weekly", today=date(2026, 6, 5))
    engine.dispose()
    assert md.startswith("# Weekly Evidence Report")
    assert "## Trade Process Review" in md


def test_event_week_briefing_lists_window_catalysts(tmp_path: Path) -> None:
    db_url = f"sqlite+pysqlite:///{tmp_path / 'r.db'}"
    engine = create_engine(db_url, future=True)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    with factory() as session:
        AccountRepository(session).create(
            name="Main Trading Account", target_value=Decimal("100000000")
        )
        EventService(session).create_event(
            EventInput(
                title="NVDA earnings",
                event_type="EARNINGS",
                date_status="TENTATIVE",
                start_date=date(2026, 6, 8),
                source="Nasdaq",
                importance_score=Decimal("4"),
            ),
            links=(EventLinkInput(ticker="NVDA", event_key="EARNINGS"),),
        )
        session.commit()
    with factory() as session:
        md = build_report_markdown(
            session, period="event-week", today=date(2026, 6, 5)
        )
    engine.dispose()
    assert md.startswith("# Event-Week Briefing")
    assert "NVDA earnings" in md
    assert "## Holdings exposure" in md
    for forbidden in _FORBIDDEN:
        assert forbidden not in md.lower()


def test_generate_report_script_writes_file(tmp_path: Path) -> None:
    db_url = f"sqlite+pysqlite:///{tmp_path / 'r.db'}"
    _seed(db_url)
    out_dir = tmp_path / "exports"
    result = subprocess.run(
        [
            "python3",
            str(REPO_ROOT / "scripts" / "generate_report.py"),
            "--period",
            "daily",
            "--date",
            "2026-06-05",
            "--out",
            str(out_dir),
        ],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        env={**os.environ, "DATABASE_URL": db_url, "FINSKILLOS_SKIP_DOTENV": "1"},
    )
    assert result.returncode == 0, result.stderr
    written = out_dir / "report_daily_2026-06-05.md"
    assert written.exists()
    assert written.read_text(encoding="utf-8").startswith("# Daily Brief")
