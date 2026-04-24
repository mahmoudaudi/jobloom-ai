from __future__ import annotations

from fastapi import APIRouter, HTTPException

from applicant_recommendation.application.dtos import RankStudentsRequest
from applicant_recommendation.application.use_cases import RankStudentsUseCase
from applicant_recommendation.infrastructure.mock_rank_students_repository import (
    MockRankStudentsRepository,
)
from api_server.settings import settings


router = APIRouter()
_rank_students_use_case = RankStudentsUseCase(MockRankStudentsRepository())


@router.post(settings.rank_students_path)
def rank_students(payload: RankStudentsRequest | None = None) -> dict:
    request = payload or RankStudentsRequest()
    try:
        return _rank_students_use_case.execute(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
