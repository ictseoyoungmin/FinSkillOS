"""Application settings for FinSkillOS v2.1.

Loads OS-style configuration from environment variables (with .env support)
and exposes a frozen Settings dataclass used across the kernel, services,
and UI layers.
"""

import os
from dataclasses import dataclass
from decimal import Decimal
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv


def _env(name: str, default: str, *aliases: str) -> str:
    """Return the first non-empty value among `name` and its aliases, else `default`."""
    for key in (name, *aliases):
        value = os.getenv(key)
        if value is not None and value != "":
            return value
    return default


@dataclass(frozen=True)
class Settings:
    app_env: str
    database_url: str
    log_level: str
    data_dir: Path
    cache_dir: Path
    export_dir: Path
    base_currency: str
    target_value: Decimal
    default_account_name: str


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    if os.getenv("FINSKILLOS_SKIP_DOTENV") != "1":
        load_dotenv()
    data_dir = Path(os.getenv("DATA_DIR", "data"))
    target_raw = _env("FINSKILLOS_TARGET_VALUE", "100000000")
    try:
        target_value = Decimal(target_raw)
    except Exception as exc:
        raise ValueError(
            f"FINSKILLOS_TARGET_VALUE must be a numeric string, got {target_raw!r}"
        ) from exc

    return Settings(
        app_env=_env("FINSKILLOS_ENV", "development", "APP_ENV"),
        database_url=os.getenv(
            "DATABASE_URL",
            "postgresql+psycopg://finskillos:finskillos_dev_password@localhost:5432/finskillos",
        ),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        data_dir=data_dir,
        cache_dir=Path(os.getenv("CACHE_DIR", str(data_dir / "cache"))),
        export_dir=Path(os.getenv("EXPORT_DIR", str(data_dir / "exports"))),
        base_currency=_env("FINSKILLOS_BASE_CURRENCY", "KRW"),
        target_value=target_value,
        default_account_name=_env(
            "FINSKILLOS_DEFAULT_ACCOUNT_NAME", "Main Trading Account"
        ),
    )


def reset_settings_cache() -> None:
    """Clear the cached Settings so tests can re-read patched env vars."""
    get_settings.cache_clear()
