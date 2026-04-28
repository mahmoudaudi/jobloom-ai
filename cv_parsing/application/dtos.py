from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class ParseCvRequest(BaseModel):
    studentUserId: Optional[str] = None
    filePath: Optional[str] = None
    fileUrl: Optional[str] = None
    fileName: Optional[str] = None
    mimeType: Optional[str] = None
    useMockData: Optional[bool] = None


class RefreshProfileSectionRequest(ParseCvRequest):
    section: str
