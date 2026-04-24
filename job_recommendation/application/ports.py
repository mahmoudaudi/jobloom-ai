from __future__ import annotations

from typing import Protocol, Sequence

from matching.models import Job, StudentProfile


class RankJobsRepository(Protocol):
    def get_mock_student(self) -> StudentProfile:
        ...

    def get_mock_jobs(self) -> Sequence[Job]:
        ...
