#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -lt 1 ]; then
  echo "Usage: bash scripts/restore_postgres.sh backups/finskillos_YYYYMMDD_HHMMSS.sql --confirm-restore" >&2
  exit 2
fi

backup_path="$1"
confirm="${2:-}"
postgres_user="${POSTGRES_USER:-finskillos}"
postgres_db="${POSTGRES_DB:-finskillos}"

if [ ! -f "${backup_path}" ]; then
  echo "Backup file not found: ${backup_path}" >&2
  exit 2
fi

if [ "${confirm}" != "--confirm-restore" ] && [ "${FINSKILLOS_CONFIRM_RESTORE:-}" != "1" ]; then
  echo "Restore is destructive for the target database." >&2
  echo "Re-run with --confirm-restore or FINSKILLOS_CONFIRM_RESTORE=1." >&2
  exit 2
fi

echo "Stopping API/web/debug-admin services before restore."
docker compose stop api web app

echo "Restoring ${backup_path} into ${postgres_db}."
docker compose exec -T postgres psql \
  -U "${postgres_user}" \
  -d "${postgres_db}" \
  < "${backup_path}"

echo "Starting API and web services after restore."
docker compose start api web

echo "Restore complete."
