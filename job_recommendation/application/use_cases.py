from __future__ import annotations

from job_recommendation.domain.ranking import rank_jobs_for_student
from .dtos import RankJobsRequest
from .mappers import to_job, to_student_profile
from .ports import RankJobsRepository
from .presenters import build_rank_jobs_response
from api_server.settings import should_use_mock_data


class RankJobsUseCase:
    def __init__(self, repository: RankJobsRepository) -> None:
        self._repository = repository

    def execute(self, payload: RankJobsRequest) -> dict:
        if should_use_mock_data(payload.useMockData):
            student = self._repository.get_mock_student()
            jobs = self._repository.get_mock_jobs()
            ranked_jobs = rank_jobs_for_student(student, jobs)
            return build_rank_jobs_response(ranked_jobs)

        if payload.student is None or not payload.jobs:
            raise ValueError("student and jobs are required when useMockData is false")

        student = to_student_profile(payload.student)
        jobs = [to_job(job) for job in payload.jobs]
        ranked_jobs = rank_jobs_for_student(student, jobs)
        return build_rank_jobs_response(ranked_jobs)
