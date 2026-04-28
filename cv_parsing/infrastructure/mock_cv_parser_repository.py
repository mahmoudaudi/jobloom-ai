from __future__ import annotations

from cv_parsing.domain.models import (
    ConfidenceInfo,
    EducationInfo,
    ExperienceInfo,
    ParsedCv,
    PersonalInfo,
)

from .mock_fixture import load_fixture


class MockCvParsingRepository:
    def get_mock_parsed_cv(self) -> ParsedCv:
        raw = load_fixture()
        return ParsedCv(
            personal=PersonalInfo(**raw.get("personal", {})),
            education=EducationInfo(**raw.get("education", {})),
            skills=list(raw.get("skills", [])),
            experiences=[ExperienceInfo(**item) for item in raw.get("experiences", [])],
            confidence=ConfidenceInfo(**raw.get("confidence", {})),
            rawText=raw.get("rawText"),
            language=str(raw.get("language", "unknown")),
        )
