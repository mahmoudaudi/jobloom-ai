from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass(frozen=True)
class ExpectedStudent:
    fullName: str = ""
    university: str = ""


@dataclass(frozen=True)
class ScheduleDocument:
    filePath: Optional[str] = None
    fileUrl: Optional[str] = None
    fileName: Optional[str] = None
    mimeType: Optional[str] = None
    documentLooksLikeSchedule: bool = False
    studentName: str = ""
    university: str = ""
    semester: str = ""
    isCurrentSemester: bool = False
    courses: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class ScheduleVerification:
    isVerified: bool
    confidence: float
    message: str
    extracted: dict
    checks: dict
    issues: List[str] = field(default_factory=list)
