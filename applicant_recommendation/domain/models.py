from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class RankedStudent:
    studentId: str
    matchPercentage: int
    matchReasons: List[str]
