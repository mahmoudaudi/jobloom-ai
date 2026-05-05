from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class ExpectedStudent:
    fullName: str = ""
    university: str = ""
    major: str = ""
    dateOfBirth: str = ""
    academicYear: str = ""


@dataclass(frozen=True)
class TranscriptDocument:
    filePath: Optional[str] = None
    fileUrl: Optional[str] = None
    fileName: Optional[str] = None
    mimeType: Optional[str] = None
    documentLooksLikeTranscript: bool = False
    documentType: str = ""
    studentName: str = ""
    university: str = ""
    degree: str = ""
    major: str = ""
    gpa: float | None = None
    lastSemester: str = ""
    academicYear: str = ""
    dateOfBirth: str = ""
    studentNumber: str = ""
    faculty: str = ""
    issuer: str = ""
    issueDate: str = ""
    referenceNumber: str = ""
    courses: list[str] = field(default_factory=list)
    hasVerificationUrl: bool = False
    hasDigitalSignature: bool = False
    hasSignatureMarker: bool = False


@dataclass(frozen=True)
class TranscriptVerification:
    isVerified: bool
    confidence: float
    message: str
    extracted: dict
    checks: dict
    issues: list[str] = field(default_factory=list)
