from __future__ import annotations

from schedule_verification.domain.models import ExpectedStudent, ScheduleDocument

from .mock_fixture import load_fixture


class MockVerifyScheduleRepository:
    def get_mock_expected_student(self) -> ExpectedStudent:
        raw = load_fixture()["expected"]
        return ExpectedStudent(
            fullName=raw.get("fullName", ""),
            university=raw.get("university", ""),
        )

    def get_mock_schedule_document(self) -> ScheduleDocument:
        raw = load_fixture()["schedule"]
        return ScheduleDocument(
            filePath=raw.get("filePath"),
            fileUrl=raw.get("fileUrl"),
            fileName=raw.get("fileName"),
            mimeType=raw.get("mimeType"),
            documentLooksLikeSchedule=bool(raw.get("documentLooksLikeSchedule")),
            studentName=raw.get("studentName", ""),
            university=raw.get("university", ""),
            semester=raw.get("semester", ""),
            isCurrentSemester=bool(raw.get("isCurrentSemester")),
            courses=list(raw.get("courses", [])),
            locations=list(raw.get("locations", [])),
        )
