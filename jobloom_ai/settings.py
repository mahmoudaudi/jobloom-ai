from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv(path: Path, *_args: object, **_kwargs: object) -> bool:
        if not path.exists():
            return False
        for line in path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or "=" not in stripped:
                continue
            key, value = stripped.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))
        return True


load_dotenv(Path(__file__).resolve().parents[1] / ".env")


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def _env_path(name: str, default: str) -> str:
    value = (os.getenv(name) or default).strip()
    if not value:
        return default
    return value if value.startswith("/") else f"/{value}"


@dataclass(frozen=True)
class Settings:
    host: str
    port: int
    reload: bool
    data_source: str
    health_path: str
    rank_jobs_path: str
    rank_students_path: str

    @property
    def use_mock_data_by_default(self) -> bool:
        return self.data_source == "mock"


settings = Settings(
    host=os.getenv("JOBLOOM_AI_HOST", "127.0.0.1"),
    port=_env_int("JOBLOOM_AI_PORT", 8000),
    reload=_env_bool("JOBLOOM_AI_RELOAD", True),
    data_source=os.getenv("JOBLOOM_AI_DATA_SOURCE", "mock").strip().lower(),
    health_path=_env_path("JOBLOOM_AI_HEALTH_PATH", "/ai/health"),
    rank_jobs_path=_env_path("JOBLOOM_AI_RANK_JOBS_PATH", "/ai/rank-jobs"),
    rank_students_path=_env_path("JOBLOOM_AI_RANK_STUDENTS_PATH", "/ai/rank-students"),
)


def should_use_mock_data(request_value: bool | None) -> bool:
    if request_value is not None:
        return request_value
    return settings.use_mock_data_by_default
