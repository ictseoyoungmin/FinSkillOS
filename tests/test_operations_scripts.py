"""Slice 14 operations script contract tests."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from finskillos.db.base import Base
from finskillos.db.repositories import NewsArticleRepository, WorkerCycleRunRepository

ROOT = Path(__file__).resolve().parents[1]
BACKUP_SCRIPT = ROOT / "scripts" / "backup_postgres.sh"
RESTORE_SCRIPT = ROOT / "scripts" / "restore_postgres.sh"
FSOCTL_SCRIPT = ROOT / "fsoctl.sh"
PYTHON_OPERATION_SCRIPTS = (
    ROOT / "scripts" / "refresh_market_data.py",
    ROOT / "scripts" / "refresh_news.py",
    ROOT / "scripts" / "calculate_indicators.py",
    ROOT / "scripts" / "refresh_worker.py",
    ROOT / "scripts" / "run_regime_scan.py",
)


def test_backup_and_restore_scripts_parse_as_bash() -> None:
    for script in (BACKUP_SCRIPT, RESTORE_SCRIPT, FSOCTL_SCRIPT):
        result = subprocess.run(
            ["bash", "-n", str(script)],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, result.stderr


def test_fsoctl_help_lists_core_commands() -> None:
    # Slice 169: the operator CLI exposes a discoverable help surface.
    result = subprocess.run(
        ["bash", str(FSOCTL_SCRIPT), "help"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    for command in ("setup", "build", "up", "down", "backup", "restore", "verify"):
        assert command in result.stdout, command


def test_fsoctl_unknown_command_exits_nonzero() -> None:
    result = subprocess.run(
        ["bash", str(FSOCTL_SCRIPT), "definitely-not-a-command"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0


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


def test_refresh_worker_contract_includes_news_refresh() -> None:
    body = (ROOT / "scripts" / "refresh_worker.py").read_text(encoding="utf-8")
    compose = (ROOT / "docker-compose.yml").read_text(encoding="utf-8")

    assert "FINSKILLOS_WORKER_INTERVAL_SECONDS" in body
    assert "FINSKILLOS_WORKER_MARKET_ENABLED" in body
    assert "FINSKILLOS_WORKER_NEWS_ENABLED" in body
    assert "FINSKILLOS_WORKER_INDICATOR_ENABLED" in body
    assert "MarketDataService" in body
    assert "NewsService" in body
    assert "build_news_feed_policy" in body
    assert "SignalService" in body
    assert "Celery" in body
    assert "redis://" not in body.lower()
    # Slice 112: the worker starts with the default `docker compose up` (no
    # longer behind the `worker` profile) after a one-shot Alembic migration.
    assert 'profiles: ["worker"]' not in compose
    assert "restart: unless-stopped" in compose
    assert "service_completed_successfully" in compose
    assert '"alembic", "upgrade", "head"' in compose
    assert "FINSKILLOS_WORKER_NEWS_ENABLED" in compose
    assert "FINSKILLOS_NEWS_RSS_FEEDS" in compose
    assert "FINSKILLOS_NEWS_RSS_TICKERS" in compose
    assert "FINSKILLOS_REFRESH_FOLDER_NAMES" in compose
    assert 'command: ["python", "scripts/refresh_worker.py"]' in compose


def test_refresh_worker_once_ingests_configured_news_feed(tmp_path) -> None:
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
      <title>MSFT AI data center update</title>
      <link>https://news.example.com/msft-ai</link>
      <pubDate>Tue, 26 May 2026 12:30:00 GMT</pubDate>
      <description>Microsoft data center spending remained in focus.</description>
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
                str(ROOT / "scripts" / "refresh_worker.py"),
                "--once",
            ],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
            env={
                **os.environ,
                "DATABASE_URL": database_url,
                "FINSKILLOS_SKIP_DOTENV": "1",
                "FINSKILLOS_WORKER_MARKET_ENABLED": "0",
                "FINSKILLOS_WORKER_NEWS_ENABLED": "1",
                "FINSKILLOS_WORKER_INDICATOR_ENABLED": "0",
                "FINSKILLOS_NEWS_RSS_FEEDS": feed_path.resolve().as_uri(),
            },
        )

        assert result.returncode == 0, result.stderr

        factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
        with factory() as session:
            rows = NewsArticleRepository(session).latest()
            assert len(rows) == 1
            assert rows[0].url == "https://news.example.com/msft-ai"
            assert rows[0].summary == "Microsoft data center spending remained in focus."
            cycles = WorkerCycleRunRepository(session).list_recent()
            assert len(cycles) == 1
            assert cycles[0].status == "OK"
            assert cycles[0].market_status == "SKIPPED"
            assert cycles[0].news_status == "OK"
            assert cycles[0].indicator_status == "SKIPPED"
    finally:
        Base.metadata.drop_all(engine)
        engine.dispose()


def test_refresh_worker_once_recomputes_regime(tmp_path) -> None:
    # AW-2: a market+indicator cycle must also recompute and persist the regime,
    # so the dashboard's headline regime stays consistent with the fresh bars
    # (previously only the manual System Ops protocol updated it).
    db_path = tmp_path / "finskillos.db"
    database_url = f"sqlite+pysqlite:///{db_path}"
    engine = create_engine(database_url, future=True)
    Base.metadata.create_all(engine)

    try:
        result = subprocess.run(
            ["python3", str(ROOT / "scripts" / "refresh_worker.py"), "--once"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
            env={
                **os.environ,
                "DATABASE_URL": database_url,
                "FINSKILLOS_SKIP_DOTENV": "1",
                "FINSKILLOS_MARKET_REFRESH_ADAPTER": "mock",
                "FINSKILLOS_WORKER_MARKET_ENABLED": "1",
                "FINSKILLOS_WORKER_NEWS_ENABLED": "0",
                "FINSKILLOS_WORKER_INDICATOR_ENABLED": "1",
            },
        )
        assert result.returncode == 0, result.stderr

        factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
        with factory() as session:
            from finskillos.db.repositories import MarketRegimeRepository

            cycles = WorkerCycleRunRepository(session).list_recent()
            assert len(cycles) == 1
            assert cycles[0].status == "OK"
            regime_section = cycles[0].summary["regime"]
            assert regime_section["enabled"] is True
            assert regime_section["status"] == "OK"
            # A regime snapshot was actually persisted by the cycle.
            assert MarketRegimeRepository(session).latest() is not None
    finally:
        Base.metadata.drop_all(engine)
        engine.dispose()


def test_refresh_worker_regime_skipped_when_indicators_disabled(tmp_path) -> None:
    # Regime follows indicators: a market-only cycle must not recompute it.
    db_path = tmp_path / "finskillos.db"
    database_url = f"sqlite+pysqlite:///{db_path}"
    engine = create_engine(database_url, future=True)
    Base.metadata.create_all(engine)

    try:
        result = subprocess.run(
            ["python3", str(ROOT / "scripts" / "refresh_worker.py"), "--once"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
            env={
                **os.environ,
                "DATABASE_URL": database_url,
                "FINSKILLOS_SKIP_DOTENV": "1",
                "FINSKILLOS_MARKET_REFRESH_ADAPTER": "mock",
                "FINSKILLOS_WORKER_MARKET_ENABLED": "1",
                "FINSKILLOS_WORKER_NEWS_ENABLED": "0",
                "FINSKILLOS_WORKER_INDICATOR_ENABLED": "0",
            },
        )
        assert result.returncode == 0, result.stderr

        factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
        with factory() as session:
            from finskillos.db.repositories import MarketRegimeRepository

            cycles = WorkerCycleRunRepository(session).list_recent()
            assert cycles[0].summary["regime"]["status"] == "SKIPPED"
            assert MarketRegimeRepository(session).latest() is None
    finally:
        Base.metadata.drop_all(engine)
        engine.dispose()


def test_refresh_worker_once_records_error_cycle_on_failure(tmp_path) -> None:
    db_path = tmp_path / "finskillos.db"
    database_url = f"sqlite+pysqlite:///{db_path}"
    engine = create_engine(database_url, future=True)
    Base.metadata.create_all(engine)

    try:
        result = subprocess.run(
            [
                "python3",
                str(ROOT / "scripts" / "refresh_worker.py"),
                "--once",
            ],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
            env={
                **os.environ,
                "DATABASE_URL": database_url,
                "FINSKILLOS_SKIP_DOTENV": "1",
                "FINSKILLOS_MARKET_REFRESH_ADAPTER": "unsupported",
                "FINSKILLOS_WORKER_MARKET_ENABLED": "1",
                "FINSKILLOS_WORKER_NEWS_ENABLED": "0",
                "FINSKILLOS_WORKER_INDICATOR_ENABLED": "0",
            },
        )

        assert result.returncode == 1

        factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
        with factory() as session:
            cycles = WorkerCycleRunRepository(session).list_recent()
            assert len(cycles) == 1
            assert cycles[0].status == "ERROR"
            assert cycles[0].market_status == "SKIPPED"
            assert cycles[0].summary is not None
            assert cycles[0].summary["error"]["type"] == "ValueError"
    finally:
        Base.metadata.drop_all(engine)
        engine.dispose()
