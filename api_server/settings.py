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


def _env_csv(name: str, default: str = "") -> tuple[str, ...]:
    value = os.getenv(name, default)
    return tuple(item.strip() for item in value.split(",") if item.strip())


@dataclass(frozen=True)
class Settings:
    host: str
    port: int
    reload: bool
    data_source: str
    health_path: str
    parse_cv_path: str
    refresh_profile_section_path: str
    verify_transcript_path: str
    rank_jobs_path: str
    rank_students_path: str
    llm_provider: str
    gemini_api_key: str
    gemini_model: str
    azure_document_intelligence_endpoint: str
    azure_document_intelligence_key: str
    llm_timeout_seconds: int
    llm_temperature: float
    llm_max_output_tokens: int
    allowed_file_hosts: tuple[str, ...]
    allow_local_file_urls: bool
    allowed_file_roots: tuple[Path, ...]
    max_remote_file_bytes: int

    @property
    def use_mock_data_by_default(self) -> bool:
        return self.data_source == "mock"


settings = Settings(
    host=os.getenv("JOBLOOM_AI_HOST", "127.0.0.1"),
    port=_env_int("JOBLOOM_AI_PORT", 8000),
    reload=_env_bool("JOBLOOM_AI_RELOAD", True),
    data_source=os.getenv("JOBLOOM_AI_DATA_SOURCE", "real").strip().lower(),
    health_path=_env_path("JOBLOOM_AI_HEALTH_PATH", "/ai/health"),
    parse_cv_path=_env_path("JOBLOOM_AI_PARSE_CV_PATH", "/ai/parse-cv"),
    refresh_profile_section_path=_env_path(
        "JOBLOOM_AI_REFRESH_PROFILE_SECTION_PATH",
        "/ai/suggest-profile-section",
    ),
    verify_transcript_path=_env_path(
        "JOBLOOM_AI_VERIFY_TRANSCRIPT_PATH",
        "/ai/verify-transcript",
    ),
    rank_jobs_path=_env_path("JOBLOOM_AI_RANK_JOBS_PATH", "/ai/rank-jobs"),
    rank_students_path=_env_path("JOBLOOM_AI_RANK_STUDENTS_PATH", "/ai/rank-students"),
    llm_provider=os.getenv("JOBLOOM_AI_LLM_PROVIDER", "mock").strip().lower(),
    gemini_api_key=os.getenv("GEMINI_API_KEY", "").strip()
    or os.getenv("JOBLOOM_AI_GEMINI_API_KEY", "").strip(),
    gemini_model=os.getenv("JOBLOOM_AI_GEMINI_MODEL", "gemini-2.5-flash").strip(),
    azure_document_intelligence_endpoint=os.getenv(
        "AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT", ""
    ).strip(),
    azure_document_intelligence_key=os.getenv(
        "AZURE_DOCUMENT_INTELLIGENCE_KEY", ""
    ).strip(),
    llm_timeout_seconds=max(_env_int("JOBLOOM_AI_LLM_TIMEOUT_SECONDS", 3), 10),
    llm_temperature=float(os.getenv("JOBLOOM_AI_LLM_TEMPERATURE", "0.2")),
    llm_max_output_tokens=_env_int("JOBLOOM_AI_LLM_MAX_OUTPUT_TOKENS", 512),
    allowed_file_hosts=_env_csv(
        "JOBLOOM_AI_ALLOWED_FILE_HOSTS",
        "jobloom-backend-service-b8axewhvcyafhtf2.swedencentral-01.azurewebsites.net",
    ),
    allow_local_file_urls=_env_bool("JOBLOOM_AI_ALLOW_LOCAL_FILE_URLS", False),
    allowed_file_roots=tuple(
        Path(value).expanduser().resolve()
        for value in _env_csv("JOBLOOM_AI_ALLOWED_FILE_ROOTS", str(Path.cwd()))
    ),
    max_remote_file_bytes=_env_int("JOBLOOM_AI_MAX_REMOTE_FILE_BYTES", 10 * 1024 * 1024),
)


def should_use_mock_data(request_value: bool | None) -> bool:
    if request_value is not None:
        return request_value
    return settings.use_mock_data_by_default
