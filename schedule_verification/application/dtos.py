from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class ExpectedStudentPayload(BaseModel):
    fullName: str = ""
    university: str = ""


class ScheduleDocumentPayload(BaseModel):
    filePath: Optional[str] = None
    fileUrl: Optional[str] = None
    fileName: Optional[str] = None
    mimeType: Optional[str] = None
    documentLooksLikeSchedule: bool = False
    studentName: str = ""
    university: str = ""
    semester: str = ""
    isCurrentSemester: bool = False
    courses: List[str] = Field(default_factory=list)
    locations: List[str] = Field(default_factory=list)


class VerifyScheduleRequest(BaseModel):
    studentUserId: Optional[str] = None
    expected: Optional[ExpectedStudentPayload] = None
    schedule: Optional[ScheduleDocumentPayload] = None
    useMockData: Optional[bool] = None
    classificationOnly: bool = False
