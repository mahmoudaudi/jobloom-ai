from __future__ import annotations

from fastapi import APIRouter, HTTPException

from api_server.settings import settings
from transcript_verification.application.dtos import VerifyTranscriptRequest
from transcript_verification.application.use_cases import VerifyTranscriptUseCase
from transcript_verification.infrastructure.local_transcript_extractor import LocalTranscriptExtractor
from transcript_verification.infrastructure.mock_verify_transcript_repository import MockVerifyTranscriptRepository


router = APIRouter()
_verify_transcript_use_case = VerifyTranscriptUseCase(
    MockVerifyTranscriptRepository(),
    extractor=LocalTranscriptExtractor(),
)


@router.post(settings.verify_transcript_path)
def verify_transcript(payload: VerifyTranscriptRequest | None = None) -> dict:
    request = payload or VerifyTranscriptRequest()
    try:
        return _verify_transcript_use_case.execute(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
