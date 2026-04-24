from __future__ import annotations

from fastapi import APIRouter, HTTPException

from job_recommendation.application.dtos import RankJobsRequest
from job_recommendation.application.use_cases import RankJobsUseCase
from job_recommendation.infrastructure.mock_rank_jobs_repository import MockRankJobsRepository
from api_server.settings import settings


router = APIRouter()
_rank_jobs_use_case = RankJobsUseCase(MockRankJobsRepository())


@router.post(settings.rank_jobs_path)
def rank_jobs(payload: RankJobsRequest | None = None) -> dict:
    request = payload or RankJobsRequest()
    try:
        return _rank_jobs_use_case.execute(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
