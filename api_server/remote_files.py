from __future__ import annotations

import tempfile
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen


def resolve_local_or_remote_path(source: str, *, prefix: str) -> Path:
    value = str(source or "").strip()
    if not value:
      raise ValueError("file source is required")

    if value.lower().startswith(("http://", "https://")):
      return _download_remote_file(value, prefix=prefix)

    path = Path(value)
    if not path.is_absolute():
        path = Path.cwd() / value.lstrip("/\\")
    if not path.exists() or not path.is_file():
        raise ValueError(f"file not found: {path}")
    return path


def _download_remote_file(url: str, *, prefix: str) -> Path:
    parsed = urlparse(url)
    suffix = Path(parsed.path).suffix or ".bin"
    with urlopen(
        Request(url, headers={"User-Agent": "Jobloom-AI/1.0"}),
        timeout=60,
    ) as response:
        data = response.read()
    with tempfile.NamedTemporaryFile(delete=False, prefix=prefix, suffix=suffix) as temp_file:
        temp_file.write(data)
        return Path(temp_file.name)
