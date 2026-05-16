from dataclasses import dataclass
import os
from pathlib import Path
from functools import lru_cache

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    app_env: str
    database_url: str
    log_level: str
    data_dir: Path
    cache_dir: Path
    export_dir: Path


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    load_dotenv()
    data_dir = Path(os.getenv("DATA_DIR", "data"))
    return Settings(
        app_env=os.getenv("APP_ENV", "development"),
        database_url=os.getenv(
            "DATABASE_URL",
            "postgresql+psycopg://finskillos:finskillos@localhost:5432/finskillos",
        ),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        data_dir=data_dir,
        cache_dir=Path(os.getenv("CACHE_DIR", str(data_dir / "cache"))),
        export_dir=Path(os.getenv("EXPORT_DIR", str(data_dir / "exports"))),
    )
