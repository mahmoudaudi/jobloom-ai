from __future__ import annotations

from schedule_verification.domain.models import ExpectedStudent, ScheduleDocument

from .dtos import ExpectedStudentPayload, ScheduleDocumentPayload


def to_expected_student(payload: ExpectedStudentPayload | None) -> ExpectedStudent:
    if payload is None:
        return ExpectedStudent()
    return ExpectedStudent(
        fullName=payload.fullName,
        university=payload.university,
    )


def to_schedule_document(payload: ScheduleDocumentPayload) -> ScheduleDocument:
    return ScheduleDocument(
        filePath=payload.filePath,
        fileUrl=payload.fileUrl,
        fileName=payload.fileName,
        mimeType=payload.mimeType,
        documentLooksLikeSchedule=payload.documentLooksLikeSchedule,
        studentName=payload.studentName,
        university=payload.university,
        semester=payload.semester,
        isCurrentSemester=payload.isCurrentSemester,
        courses=payload.courses,
        locations=payload.locations,
    )
