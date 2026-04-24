from __future__ import annotations

from typing import Protocol, Sequence

from matching.models import Job, StudentProfile


class RankStudentsRepository(Protocol):
    def get_mock_job(self) -> Job:
        ...

    def get_mock_students(self) -> Sequence[StudentProfile]:
        ...
