from __future__ import annotations

from api_server.settings import should_use_mock_data
from transcript_verification.domain.verification import verify_transcript

from .dtos import VerifyTranscriptRequest
from .mappers import to_expected_student, to_transcript_document
from .ports import TranscriptVerificationRepository
from .presenters import build_verify_transcript_response


class VerifyTranscriptUseCase:
    def __init__(self, repository: TranscriptVerificationRepository, extractor=None) -> None:
        self._repository = repository
        self._extractor = extractor

    def execute(self, payload: VerifyTranscriptRequest) -> dict:
        if should_use_mock_data(payload.useMockData):
            result = verify_transcript(
                self._repository.get_mock_transcript_document(),
                self._repository.get_mock_expected_student(),
            )
            return build_verify_transcript_response(result)

        if payload.transcript is None:
            raise ValueError("transcript is required when useMockData is false")
        transcript = payload.transcript
        has_file_reference = bool(transcript.filePath or transcript.fileUrl)
        has_complete_extraction = bool(
            transcript.documentLooksLikeTranscript
            and transcript.university.strip()
            and (transcript.gpa is not None or transcript.courses)
        )

        if has_file_reference and not has_complete_extraction:
            if self._extractor is None:
                raise ValueError("transcript extracted fields are required when no extractor is configured")
            transcript = self._extractor.extract(transcript)

        if payload.expected is None:
            raise ValueError("expected is required when useMockData is false")

        result = verify_transcript(
            to_transcript_document(transcript),
            to_expected_student(payload.expected),
        )
        return build_verify_transcript_response(result)

