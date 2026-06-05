"""Runtime environment overlay helpers.

The process boots with base values from ``os.environ`` so existing `.env`-
behavior stays intact. If a row exists in ``system_ops_settings`` it is loaded and
merged on top as an override layer.

This keeps startup deterministic while allowing Operators to persist runtime
settings from the System Ops tab. If DB reads fail, overlay is skipped and env
defaults are used.
"""

from __future__ import annotations

import os
from collections.abc import Iterable, Mapping
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

_ALLOWED_SETTING_KEYS = {
    "FINSKILLOS_WORKER_INTERVAL_SECONDS",
    "FINSKILLOS_WORKER_POLL_SECONDS",
    "FINSKILLOS_WORKER_STALE_GRACE_SECONDS",
    "FINSKILLOS_WORKER_RUN_ON_START",
    "FINSKILLOS_WORKER_MARKET_ENABLED",
    "FINSKILLOS_WORKER_NEWS_ENABLED",
    "FINSKILLOS_WORKER_INDICATOR_ENABLED",
    "FINSKILLOS_WORKER_REGIME_ENABLED",
    "FINSKILLOS_WORKER_RUNNING_STALE_SECONDS",
    "FINSKILLOS_WORKER_PERSIST_INDICATOR_HISTORY",
    "FINSKILLOS_MARKET_REFRESH_ADAPTER",
    "FINSKILLOS_MARKET_FETCH_RETRIES",
    "FINSKILLOS_MARKET_FETCH_BACKOFF_SECONDS",
    "FINSKILLOS_MARKET_REFRESH_TICKERS",
    "FINSKILLOS_INDICATOR_REFRESH_TICKERS",
    "FINSKILLOS_MARKET_REFRESH_TIMEFRAME",
    "FINSKILLOS_REFRESH_FOLDER_NAMES",
    "FINSKILLOS_NEWS_REFRESH_ADAPTER",
    "FINSKILLOS_NEWS_RSS_FEEDS",
    "FINSKILLOS_NEWS_RSS_TICKERS",
    "FINSKILLOS_NEWS_RSS_SOURCE",
    "FINSKILLOS_NEWS_RSS_LANGUAGE",
    # v3 Phase 10: the active LLM provider for the agent narrator (Ops switcher).
    "FINSKILLOS_LLM_PROVIDER",
}

_ALLOWED_SETTING_KEYS_TUPLE = tuple(sorted(_ALLOWED_SETTING_KEYS))
_BOOL_TRUE = {"1", "true", "yes", "on", "y", "enabled"}


def allowed_setting_keys() -> tuple[str, ...]:
    """Return the canonical list of persistable runtime keys."""

    return _ALLOWED_SETTING_KEYS_TUPLE


def _coerce_str(raw: str | None) -> str | None:
    if raw is None:
        return None
    text = raw.strip()
    return text if text != "" else None


def _read_overrides(session: Session | None = None) -> dict[str, str]:
    """Read stored setting overrides from DB.

    Returns an immutable copy so callers can mutate returned values freely.
    """

    if session is not None:
        try:
            from finskillos.db.repositories import SystemOpsSettingsRepository

            values = SystemOpsSettingsRepository(session).get().values or {}
            return {
                key: str(value)
                for key, value in values.items()
                if key in _ALLOWED_SETTING_KEYS and _coerce_str(str(value)) is not None
            }
        except Exception:
            return {}

    try:
        from finskillos.db.session import session_scope

        with session_scope() as nested_session:
            if nested_session is None:
                return {}
            from finskillos.db.repositories import SystemOpsSettingsRepository

            values = SystemOpsSettingsRepository(nested_session).get().values or {}
            return {
                key: str(value)
                for key, value in values.items()
                if key in _ALLOWED_SETTING_KEYS and _coerce_str(str(value)) is not None
            }
    except Exception:
        return {}


def _read_overlay_audit(
    session: Session | None = None,
) -> tuple[str | None, str | None]:
    """Return (updated_at_iso, updated_by) of the DB overlay row, or (None, None).

    Surfaces who/when last changed the runtime overlay so the cockpit can show it
    (the row is a single document; this is last-change metadata, not per-key
    history)."""

    def _extract(active_session: Session) -> tuple[str | None, str | None]:
        from finskillos.db.repositories import SystemOpsSettingsRepository

        row = SystemOpsSettingsRepository(active_session).get()
        if not row.values:
            # No overrides stored → nothing has been changed from env defaults.
            return None, None
        updated_at = row.updated_at.isoformat() if row.updated_at else None
        return updated_at, row.updated_by

    if session is not None:
        try:
            return _extract(session)
        except Exception:
            return None, None
    try:
        from finskillos.db.session import session_scope

        with session_scope() as nested_session:
            if nested_session is None:
                return None, None
            return _extract(nested_session)
    except Exception:
        return None, None


def _read_overlay_history(
    session: Session | None = None, *, limit: int = 20
) -> list[dict[str, str | None]]:
    """Recent runtime-setting changes (newest first), for the cockpit history list."""

    def _extract(active_session: Session) -> list[dict[str, str | None]]:
        from finskillos.db.repositories import SystemOpsSettingsRepository

        rows = SystemOpsSettingsRepository(active_session).list_history(limit=limit)
        return [
            {
                "key": row.setting_key,
                "old_value": row.old_value,
                "new_value": row.new_value,
                "updated_by": row.updated_by,
                "changed_at": row.created_at.isoformat() if row.created_at else None,
            }
            for row in rows
        ]

    if session is not None:
        try:
            return _extract(session)
        except Exception:
            return []
    try:
        from finskillos.db.session import session_scope

        with session_scope() as nested_session:
            if nested_session is None:
                return []
            return _extract(nested_session)
    except Exception:
        return []


def read_runtime_value(
    name: str,
    *,
    default: str | None = None,
    session: Session | None = None,
    runtime_overrides: Mapping[str, str] | None = None,
    include_empty: bool = False,
) -> str | None:
    """Return an env-backed value with DB override if present.

    :param include_empty:
        When False (default), empty strings from env or DB are treated as unset.
    """

    if name not in _ALLOWED_SETTING_KEYS:
        raise ValueError(f"unsupported runtime setting key: {name}")

    if runtime_overrides is not None and name in runtime_overrides:
        value = _coerce_str(str(runtime_overrides[name]))
        if value is None:
            return default
        return value if (include_empty or value) else None

    db_overrides = _read_overrides(session)
    if name in db_overrides:
        value = _coerce_str(db_overrides[name])
        if value is not None:
            return value if (include_empty or value) else None

    raw = os.getenv(name)
    if raw is None:
        return default

    text = raw.strip()
    if not include_empty and text == "":
        return default
    return text if text != "" else default


def read_runtime_bool(
    name: str,
    *,
    default: bool,
    session: Session | None = None,
    runtime_overrides: Mapping[str, str] | None = None,
) -> bool:
    raw = read_runtime_value(
        name,
        default=str(int(default)),
        session=session,
        runtime_overrides=runtime_overrides,
    )
    if raw is None:
        return default

    text = raw.strip().lower()
    if text == "":
        return default
    return text in _BOOL_TRUE


def read_runtime_int(
    name: str,
    *,
    default: int,
    minimum: int = 1,
    session: Session | None = None,
    runtime_overrides: Mapping[str, str] | None = None,
) -> int:
    raw = read_runtime_value(
        name,
        default=str(default),
        session=session,
        runtime_overrides=runtime_overrides,
    )
    if raw is None:
        return default

    try:
        value = int(raw)
    except (TypeError, ValueError):
        return default
    if value < minimum:
        return minimum
    return value


def read_runtime_csv(
    name: str,
    *,
    session: Session | None = None,
    runtime_overrides: Mapping[str, str] | None = None,
) -> tuple[str, ...]:
    raw = read_runtime_value(
        name,
        default="",
        session=session,
        runtime_overrides=runtime_overrides,
    )
    if raw is None:
        return ()
    return tuple(part.strip() for part in raw.replace(";", ",").split(",") if part.strip())


def runtime_settings_snapshot(
    *,
    session: Session | None = None,
    keys: Iterable[str] | None = None,
    defaults: dict[str, str] | None = None,
    runtime_overrides: Mapping[str, str] | None = None,
) -> dict[str, str]:
    """Return effective runtime values for the requested keys.

    Missing values are filled from ``defaults`` (when provided) and then omitted
    when neither env nor override provides content.
    """

    selected = keys or _ALLOWED_SETTING_KEYS
    defaults = defaults or {}
    output: dict[str, str] = {}

    for name in selected:
        if name not in _ALLOWED_SETTING_KEYS:
            continue

        value = read_runtime_value(
            name,
            default=defaults.get(name),
            session=session,
            runtime_overrides=runtime_overrides,
        )
        if value is not None:
            output[name] = value
    return output


def runtime_setting_snapshot_for_job_queue(
    *,
    session: Session | None = None,
) -> dict[str, str]:
    """Return compact metadata payload for job rows.

    Uses a deterministic sort order to keep audit records easy to diff.
    """

    return {
        key: value
        for key, value in sorted(
            runtime_settings_snapshot(session=session).items(),
            key=lambda item: item[0],
        )
    }


def runtime_overlay_meta(*, session: Session | None = None) -> dict[str, Any]:
    """Build System Ops settings card metadata for payloads."""

    overrides = _read_overrides(session)
    values = runtime_settings_snapshot(session=session)
    updated_at, updated_by = _read_overlay_audit(session)

    return {
        "values": values,
        "overrides": overrides,
        "captured_at": datetime.now(tz=timezone.utc).isoformat(timespec="seconds"),
        "updated_at": updated_at,
        "updated_by": updated_by,
        "history": _read_overlay_history(session),
    }


__all__ = [
    "allowed_setting_keys",
    "read_runtime_bool",
    "read_runtime_csv",
    "read_runtime_int",
    "read_runtime_value",
    "runtime_overlay_meta",
    "runtime_settings_snapshot",
    "runtime_setting_snapshot_for_job_queue",
]
