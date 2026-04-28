from __future__ import annotations

from api_server.settings import should_use_mock_data
from schedule_verification.domain.models import ScheduleVerification
from schedule_verification.domain.verification import verify_schedule

from .dtos import VerifyScheduleRequest
from .mappers import to_expected_student, to_schedule_document
from .ports import ScheduleVerificationRepository
from .presenters import build_verify_schedule_response


class VerifyScheduleUseCase:
    def __init__(self, repository: ScheduleVerificationRepository, extractor=None) -> None:
        self._repository = repository
        self._extractor = extractor

    def execute(self, payload: VerifyScheduleRequest) -> dict:
        if should_use_mock_data(payload.useMockData):
            result = verify_schedule(
                self._repository.get_mock_schedule_document(),
                self._repository.get_mock_expected_student(),
            )
            return build_verify_schedule_response(result)

        if payload.schedule is None:
            raise ValueError("schedule is required when useMockData is false")

        schedule = payload.schedule
        has_file_reference = bool(schedule.filePath or schedule.fileUrl)
        has_complete_extraction = (
            schedule.documentLooksLikeSchedule
            and bool(schedule.studentName.strip())
            and bool(schedule.university.strip())
            and bool(schedule.courses)
        )

        if payload.classificationOnly:
            classification_reason = ""
            confidence = 1.0 if schedule.documentLooksLikeSchedule else 0.0
            is_schedule = bool(schedule.documentLooksLikeSchedule)

            if has_file_reference:
                if self._extractor is None:
                    raise ValueError("schedule classifier is not configured")
                if hasattr(self._extractor, "classify_document"):
                    classification = self._extractor.classify_document(schedule)
                    is_schedule = bool(classification.get("isSchedule"))
                    try:
                        confidence = float(
                            classification.get("confidence", 1.0 if is_schedule else 0.0)
                        )
                    except (TypeError, ValueError):
                        confidence = 1.0 if is_schedule else 0.0
                    classification_reason = str(classification.get("reason") or "").strip()
                else:
                    schedule = self._extractor.extract(schedule)
                    is_schedule = bool(schedule.documentLooksLikeSchedule)
                    confidence = 1.0 if is_schedule else 0.0

            result = ScheduleVerification(
                isVerified=is_schedule,
                confidence=confidence,
                message=(
                    "Document appears to be a class schedule."
                    if is_schedule
                    else "Document does not appear to be a class schedule."
                ),
                extracted={
                    "studentName": schedule.studentName,
                    "university": schedule.university,
                    "semester": schedule.semester,
                    "courses": schedule.courses,
                    "filePath": schedule.filePath,
                    "fileUrl": schedule.fileUrl,
                    "fileName": schedule.fileName,
                    "mimeType": schedule.mimeType,
                    "classificationReason": classification_reason,
                },
                checks={
                    "documentLooksLikeSchedule": is_schedule,
                },
                issues=[] if is_schedule else ["documentLooksLikeSchedule"],
            )
            return build_verify_schedule_response(result)

        if has_file_reference and not has_complete_extraction:
            if self._extractor is None:
                raise ValueError("schedule extracted fields are required when no extractor is configured")
            schedule = self._extractor.extract(schedule)

        if payload.expected is None:
            raise ValueError("expected is required unless classificationOnly is true")

        result = verify_schedule(
            to_schedule_document(schedule),
            to_expected_student(payload.expected),
        )
        return build_verify_schedule_response(result)
