from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class ExpectedStudentPayload(BaseModel):
    fullName: str = ""
    university: str = ""
    major: str = ""


class TranscriptDocumentPayload(BaseModel):
    filePath: Optional[str] = None
    fileUrl: Optional[str] = None
    fileName: Optional[str] = None
    mimeType: Optional[str] = None
    documentLooksLikeTranscript: bool = False
    studentName: str = ""
    university: str = ""
    degree: str = ""
    major: str = ""
    gpa: float | None = None
    lastSemester: str = ""
    courses: list[str] = Field(default_factory=list)
    hasVerificationUrl: bool = False
    hasDigitalSignature: bool = False


class VerifyTranscriptRequest(BaseModel):
    studentUserId: Optional[str] = None
    expected: Optional[ExpectedStudentPayload] = None
    transcript: Optional[TranscriptDocumentPayload] = None
    useMockData: Optional[bool] = None

