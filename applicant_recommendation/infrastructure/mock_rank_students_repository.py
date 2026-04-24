from __future__ import annotations

from matching.mappers import job_from_raw, student_from_raw
from matching.models import Job, StudentProfile
from .mock_fixture import load_fixture


class MockRankStudentsRepository:
    def get_mock_job(self) -> Job:
        return job_from_raw(load_fixture()["job"])

    def get_mock_students(self) -> list[StudentProfile]:
        return [student_from_raw(item) for item in load_fixture()["students"]]
