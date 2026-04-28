from __future__ import annotations

from typing import Protocol

from cv_parsing.domain.models import ParsedCv


class CvParsingRepository(Protocol):
    def get_mock_parsed_cv(self) -> ParsedCv:
        ...
