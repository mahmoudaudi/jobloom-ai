from __future__ import annotations

from applicant_recommendation.domain.ranking import rank_students_for_job
from api_server.settings import should_use_mock_data
from .dtos import RankStudentsRequest
from .mappers import to_job, to_student_profile
from .ports import RankStudentsRepository
from .presenters import build_rank_students_response


class RankStudentsUseCase:
    def __init__(self, repository: RankStudentsRepository) -> None:
        self._repository = repository

    def execute(self, payload: RankStudentsRequest) -> dict:
        if should_use_mock_data(payload.useMockData):
            job = self._repository.get_mock_job()
            students = self._repository.get_mock_students()
            ranked_students = rank_students_for_job(job, students)
            return build_rank_students_response(ranked_students)

        if payload.job is None or not payload.students:
            raise ValueError("job and students are required when useMockData is false")

        job = to_job(payload.job)
        students = [to_student_profile(student) for student in payload.students]
        ranked_students = rank_students_for_job(job, students)
        return build_rank_students_response(ranked_students)
