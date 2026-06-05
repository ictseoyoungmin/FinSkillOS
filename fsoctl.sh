#!/usr/bin/env bash
#
# fsoctl.sh — FinSkillOS local operator CLI (Slice 169).
#
# One entrypoint over `docker compose` for the personal-deployment workflow:
# first-time setup, daily start/stop, refresh, backup/restore, and the Docker
# verification gate. Wraps the commands documented in docs/OPERATIONS_RUNBOOK.md
# so there is a single, discoverable surface.
#
# This is operator tooling — it never trades; the product stays descriptive.

set -euo pipefail

# Run from the repo root regardless of where the caller is.
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${ROOT_DIR}"

COMPOSE="docker compose"
# App-code services baked at build time (no source bind-mount): rebuild these
# before any verification or a post-edit `up`, or stale image content runs.
APP_SERVICES="api web worker migrate"

c_blue() { printf '\033[34m%s\033[0m\n' "$*"; }
c_warn() { printf '\033[33m%s\033[0m\n' "$*" >&2; }
die() { printf '\033[31merror:\033[0m %s\n' "$*" >&2; exit 1; }

usage() {
  cat <<'USAGE'
fsoctl.sh — FinSkillOS local operator CLI

Usage: ./fsoctl.sh <command> [args]

Setup / lifecycle
  setup            First-time: build, start DB, migrate, seed sample data, start stack
  build            Rebuild app images (api web worker migrate) — run before verify / up after edits
  up | start       Start the full stack in the background (brings up deps)
  down | stop      Stop the stack (keeps the database volume / data)
  restart [svc]    Restart everything, or one service
  status           Show service states (docker compose ps)
  logs [svc]       Follow logs (all services, or one)

Data / operations
  migrate          Apply database migrations (alembic upgrade head)
  seed             Seed the sample account + System folder (idempotent)
  refresh          Run one refresh cycle now (market → news → indicators → regime)
  backup [path]    Back up Postgres to backups/ (or the given path)
  restore <file>   Restore Postgres from a dump (requires --confirm-restore; destructive)

Verification
  verify           Rebuild app images, then run the Docker test gate (pytest + ruff)

  help             Show this help

Examples
  ./fsoctl.sh setup
  ./fsoctl.sh up && ./fsoctl.sh status
  ./fsoctl.sh backup
  ./fsoctl.sh restore backups/finskillos_20260604_120000.sql --confirm-restore
USAGE
}

cmd_build() {
  c_blue "Rebuilding app images: ${APP_SERVICES}"
  ${COMPOSE} build ${APP_SERVICES}
}

cmd_migrate() {
  c_blue "Applying database migrations"
  ${COMPOSE} up -d postgres
  ${COMPOSE} run --rm migrate
}

cmd_seed() {
  c_blue "Seeding sample account + System folder (idempotent)"
  ${COMPOSE} up -d postgres
  ${COMPOSE} run --rm api python -m scripts.seed_sample_data
}

cmd_setup() {
  cmd_build
  cmd_migrate
  cmd_seed
  cmd_up
  c_blue "Setup complete — open http://localhost:5173"
}

cmd_up() {
  c_blue "Starting the stack"
  ${COMPOSE} up -d
}

cmd_down() {
  c_blue "Stopping the stack (database volume is preserved)"
  ${COMPOSE} stop
}

cmd_restart() {
  if [ "$#" -ge 1 ]; then
    ${COMPOSE} restart "$1"
  else
    ${COMPOSE} restart
  fi
}

cmd_status() {
  ${COMPOSE} ps
}

cmd_logs() {
  if [ "$#" -ge 1 ]; then
    ${COMPOSE} logs -f "$1"
  else
    ${COMPOSE} logs -f
  fi
}

cmd_refresh() {
  c_blue "Running one refresh cycle"
  ${COMPOSE} up -d postgres
  ${COMPOSE} run --rm worker python scripts/refresh_worker.py --once
}

cmd_backup() {
  bash scripts/backup_postgres.sh "$@"
}

cmd_restore() {
  [ "$#" -ge 1 ] || die "restore requires a dump file: ./fsoctl.sh restore <file> --confirm-restore"
  bash scripts/restore_postgres.sh "$@"
}

cmd_verify() {
  cmd_build
  c_blue "Running the Docker test gate"
  ${COMPOSE} run --rm --no-deps api pytest \
    tests/test_api_v42_contract.py tests/test_api_health.py \
    tests/test_api_system_ops.py tests/test_operations_scripts.py -q
  ${COMPOSE} run --rm --no-deps api ruff check api finskillos tests
  ${COMPOSE} run --rm --no-deps web npm run build
  c_blue "Verification complete"
}

main() {
  local command="${1:-help}"
  [ "$#" -ge 1 ] && shift || true
  case "${command}" in
    setup) cmd_setup "$@" ;;
    build) cmd_build "$@" ;;
    up | start) cmd_up "$@" ;;
    down | stop) cmd_down "$@" ;;
    restart) cmd_restart "$@" ;;
    status) cmd_status "$@" ;;
    logs) cmd_logs "$@" ;;
    migrate) cmd_migrate "$@" ;;
    seed) cmd_seed "$@" ;;
    refresh) cmd_refresh "$@" ;;
    backup) cmd_backup "$@" ;;
    restore) cmd_restore "$@" ;;
    verify) cmd_verify "$@" ;;
    help | -h | --help) usage ;;
    *) c_warn "unknown command: ${command}"; usage; exit 2 ;;
  esac
}

main "$@"
