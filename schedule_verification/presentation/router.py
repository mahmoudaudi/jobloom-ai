from __future__ import annotations

from fastapi import APIRouter, HTTPException

from api_server.settings import settings
from schedule_verification.application.dtos import VerifyScheduleRequest
from schedule_verification.application.use_cases import VerifyScheduleUseCase
from schedule_verification.infrastructure.gemini_schedule_extractor import (
    build_schedule_extractor,
)
from schedule_verification.infrastructure.mock_verify_schedule_repository import (
    MockVerifyScheduleRepository,
)


router = APIRouter()
_verify_schedule_use_case = VerifyScheduleUseCase(
    MockVerifyScheduleRepository(),
    extractor=build_schedule_extractor(),
)


@router.post(settings.verify_schedule_path)
def verify_schedule(payload: VerifyScheduleRequest | None = None) -> dict:
    request = payload or VerifyScheduleRequest()
    try:
        return _verify_schedule_use_case.execute(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
