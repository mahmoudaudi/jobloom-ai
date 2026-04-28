from __future__ import annotations

from typing import Protocol

from transcript_verification.domain.models import ExpectedStudent, TranscriptDocument


class TranscriptVerificationRepository(Protocol):
    def get_mock_expected_student(self) -> ExpectedStudent:
        ...

    def get_mock_transcript_document(self) -> TranscriptDocument:
        ...

