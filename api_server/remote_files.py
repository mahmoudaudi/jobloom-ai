from __future__ import annotations

import tempfile
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from api_server.settings import settings


LOCAL_FILE_HOSTS = {"localhost", "127.0.0.1", "::1"}


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def resolve_local_or_remote_path(source: str, *, prefix: str) -> Path:
    value = str(source or "").strip()
    if not value:
      raise ValueError("file source is required")

    if value.lower().startswith(("http://", "https://")):
      return _download_remote_file(value, prefix=prefix)

    path = Path(value).expanduser()
    if not path.is_absolute():
        path = Path.cwd() / value.lstrip("/\\")
    path = path.resolve()
    if not any(_is_relative_to(path, root) for root in settings.allowed_file_roots):
        raise ValueError("file path is outside allowed roots")
    if not path.exists() or not path.is_file():
        raise ValueError(f"file not found: {path}")
    return path


def _is_allowed_remote_host(hostname: str) -> bool:
    host = hostname.strip().lower()
    allowed_hosts = {item.lower() for item in settings.allowed_file_hosts}
    if host in allowed_hosts:
        return True
    return settings.allow_local_file_urls and host in LOCAL_FILE_HOSTS


def _download_remote_file(url: str, *, prefix: str) -> Path:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("remote file URL must be http or https")
    if not _is_allowed_remote_host(parsed.hostname):
        raise ValueError("remote file host is not allowed")

    suffix = Path(parsed.path).suffix or ".bin"
    with urlopen(
        Request(url, headers={"User-Agent": "Jobloom-AI/1.0"}),
        timeout=60,
    ) as response:
        final_url = urlparse(response.geturl())
        if (
            final_url.scheme not in {"http", "https"}
            or not final_url.hostname
            or not _is_allowed_remote_host(final_url.hostname)
        ):
            raise ValueError("remote file redirect target is not allowed")
        content_length = response.headers.get("Content-Length")
        if content_length and int(content_length) > settings.max_remote_file_bytes:
            raise ValueError("remote file is too large")
        data = response.read(settings.max_remote_file_bytes + 1)
        if len(data) > settings.max_remote_file_bytes:
            raise ValueError("remote file is too large")
    with tempfile.NamedTemporaryFile(delete=False, prefix=prefix, suffix=suffix) as temp_file:
        temp_file.write(data)
        return Path(temp_file.name)
