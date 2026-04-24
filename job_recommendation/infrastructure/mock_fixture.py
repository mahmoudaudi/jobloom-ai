from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path


FIXTURE_PATH = Path(__file__).resolve().parent / "mock_rank_jobs.json"


@lru_cache(maxsize=1)
def load_fixture() -> dict:
    with FIXTURE_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)
