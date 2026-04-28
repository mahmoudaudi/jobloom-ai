from __future__ import annotations

from typing import Protocol

from schedule_verification.domain.models import ExpectedStudent, ScheduleDocument


class ScheduleVerificationRepository(Protocol):
    def get_mock_expected_student(self) -> ExpectedStudent:
        ...

    def get_mock_schedule_document(self) -> ScheduleDocument:
        ...
