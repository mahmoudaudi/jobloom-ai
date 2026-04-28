from __future__ import annotations

from .dtos import ParseCvRequest
from .presenters import build_parse_cv_response


class ParseCvUseCase:
    def __init__(self, extractor=None) -> None:
        self._extractor = extractor

    def execute(self, payload: ParseCvRequest) -> dict:
        parsed = self.parse(payload)
        return build_parse_cv_response(parsed)

    def parse(self, payload: ParseCvRequest):
        if payload.useMockData:
            raise ValueError("mock data is not supported for parse-cv")

        if not (payload.filePath or payload.fileUrl):
            raise ValueError("filePath or fileUrl is required")
        if self._extractor is None:
            raise ValueError("cv extractor is not configured")

        return self._extractor.extract(payload)
