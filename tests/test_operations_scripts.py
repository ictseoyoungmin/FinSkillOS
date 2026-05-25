"""Slice 14 operations script contract tests."""

from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKUP_SCRIPT = ROOT / "scripts" / "backup_postgres.sh"
RESTORE_SCRIPT = ROOT / "scripts" / "restore_postgres.sh"


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
    assert "backups/*.sql" in gitignore
    assert (ROOT / "backups" / ".gitkeep").exists()
