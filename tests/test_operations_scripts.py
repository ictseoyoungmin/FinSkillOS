"""Slice 14 operations script contract tests."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from finskillos.db.base import Base
from finskillos.db.repositories import NewsArticleRepository

ROOT = Path(__file__).resolve().parents[1]
BACKUP_SCRIPT = ROOT / "scripts" / "backup_postgres.sh"
RESTORE_SCRIPT = ROOT / "scripts" / "restore_postgres.sh"
PYTHON_OPERATION_SCRIPTS = (
    ROOT / "scripts" / "refresh_market_data.py",
    ROOT / "scripts" / "refresh_news.py",
    ROOT / "scripts" / "calculate_indicators.py",
    ROOT / "scripts" / "refresh_worker.py",
    ROOT / "scripts" / "run_regime_scan.py",
)


def test_backup_and_restore_scripts_parse_as_bash() -> None:
    for script in (BACKUP_SCRIPT, RESTORE_SCRIPT):
        result = subprocess.run(
            ["bash", "-n", str(script)],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, result.stderr


def test_python_operation_scripts_expose_help() -> None:
    for script in PYTHON_OPERATION_SCRIPTS:
        result = subprocess.run(
            ["python3", str(script), "--help"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, result.stderr
        assert "usage:" in result.stdout


def test_market_refresh_script_exposes_yahoo_adapter_option() -> None:
    body = (ROOT / "scripts" / "refresh_market_data.py").read_text(encoding="utf-8")

    assert 'choices=("mock", "csv", "yahoo")' in body
    assert "YahooChartMarketDataAdapter" in body
    assert "--adapter yahoo" in body


def test_news_refresh_script_exposes_rss_adapter_options() -> None:
    body = (ROOT / "scripts" / "refresh_news.py").read_text(encoding="utf-8")

    assert 'choices=("rss",)' in body
    assert "RssNewsAdapter" in body
    assert "--feed-url" in body
    assert "--feed-file" in body
    assert "does not crawl article bodies" in body


def test_news_refresh_script_ingests_local_feed_file(tmp_path) -> None:
    db_path = tmp_path / "finskillos.db"
    database_url = f"sqlite+pysqlite:///{db_path}"
    engine = create_engine(database_url, future=True)
    Base.metadata.create_all(engine)
    feed_path = tmp_path / "feed.xml"
    feed_path.write_text(
        """\
<rss version="2.0">
  <channel>
    <title>Market Desk</title>
    <item>
      <title>AAPL AI infrastructure update</title>
      <link>https://news.example.com/aapl-ai</link>
      <pubDate>Tue, 26 May 2026 12:30:00 GMT</pubDate>
      <description>Apple data center investment remained in focus.</description>
    </item>
  </channel>
</rss>
""",
        encoding="utf-8",
    )

    try:
        result = subprocess.run(
            [
                "python3",
                str(ROOT / "scripts" / "refresh_news.py"),
                "--feed-file",
                str(feed_path),
                "--json",
            ],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
            env={
                **os.environ,
                "DATABASE_URL": database_url,
                "FINSKILLOS_SKIP_DOTENV": "1",
            },
        )

        assert result.returncode == 0, result.stderr
        assert '"articlesIngested": 1' in result.stdout

        factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
        with factory() as session:
            rows = NewsArticleRepository(session).latest()
            assert len(rows) == 1
            assert rows[0].url == "https://news.example.com/aapl-ai"
            assert rows[0].summary == "Apple data center investment remained in focus."
    finally:
        Base.metadata.drop_all(engine)
        engine.dispose()


def test_restore_script_requires_explicit_confirmation() -> None:
    body = RESTORE_SCRIPT.read_text(encoding="utf-8")
    assert "--confirm-restore" in body
    assert "FINSKILLOS_CONFIRM_RESTORE" in body
    assert "Restore is destructive" in body


def test_backup_outputs_to_ignored_backups_directory() -> None:
    body = BACKUP_SCRIPT.read_text(encoding="utf-8")
    gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")

    assert 'backup_dir="${BACKUP_DIR:-backups}"' in body
    assert "pg_dump" in body
    assert "--clean" in body
    assert "--if-exists" in body
    assert "backups/*.sql" in gitignore
    assert (ROOT / "backups" / ".gitkeep").exists()


def test_restore_script_uses_confirmed_clean_restore() -> None:
    body = RESTORE_SCRIPT.read_text(encoding="utf-8")

    assert "DROP SCHEMA IF EXISTS public CASCADE" in body
    assert "CREATE SCHEMA public" in body
    assert "ON_ERROR_STOP=1" in body
    assert "clean restore" in body


def test_refresh_policy_document_tracks_script_order() -> None:
    body = (
        ROOT / "docs" / "v2_1" / "11_Scheduler_Refresh_Policy.md"
    ).read_text(encoding="utf-8")

    assert "scripts/refresh_market_data.py" in body
    assert "scripts/calculate_indicators.py" in body
    assert "scripts/refresh_worker.py" in body
    assert "scripts/run_regime_scan.py" in body
    assert "Do not add Celery" in body


def test_refresh_worker_contract_is_lightweight_and_news_deferred() -> None:
    body = (ROOT / "scripts" / "refresh_worker.py").read_text(encoding="utf-8")
    compose = (ROOT / "docker-compose.yml").read_text(encoding="utf-8")

    assert "FINSKILLOS_WORKER_INTERVAL_SECONDS" in body
    assert "FINSKILLOS_WORKER_MARKET_ENABLED" in body
    assert "FINSKILLOS_WORKER_INDICATOR_ENABLED" in body
    assert "MarketDataService" in body
    assert "SignalService" in body
    assert "Celery" in body
    assert "redis://" not in body.lower()
    assert 'profiles: ["worker"]' in compose
    assert 'command: ["python", "scripts/refresh_worker.py"]' in compose
