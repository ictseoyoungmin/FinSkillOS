#!/usr/bin/env bash
set -euo pipefail

backup_dir="${BACKUP_DIR:-backups}"
postgres_user="${POSTGRES_USER:-finskillos}"
postgres_db="${POSTGRES_DB:-finskillos}"
timestamp="$(date -u +%Y%m%d_%H%M%S)"
output_path="${1:-${backup_dir}/finskillos_${timestamp}.sql}"

mkdir -p "$(dirname "${output_path}")"

echo "Creating Postgres backup: ${output_path}"
docker compose exec -T postgres pg_dump \
  -U "${postgres_user}" \
  -d "${postgres_db}" \
  > "${output_path}"

echo "Backup complete: ${output_path}"
