from __future__ import annotations

from matching.mappers import job_from_raw, student_from_raw
from matching.models import Job, StudentProfile
from .mock_fixture import load_fixture


class MockRankJobsRepository:
    def get_mock_student(self) -> StudentProfile:
        return student_from_raw(load_fixture()["student"])

    def get_mock_jobs(self) -> list[Job]:
        return [job_from_raw(item) for item in load_fixture()["jobs"]]
