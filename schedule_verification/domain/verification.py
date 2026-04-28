from __future__ import annotations

import re
from datetime import UTC, datetime
from difflib import SequenceMatcher

from .models import ExpectedStudent, ScheduleDocument, ScheduleVerification


SUPPORTED_EXTENSIONS = (".pdf", ".png", ".jpg", ".jpeg", ".webp")
SUPPORTED_MIME_TYPES = ("application/pdf", "image/png", "image/jpeg", "image/webp")
SEMESTER_KEYWORDS = {
    "spring": "spring",
    "fall": "fall",
    "autumn": "fall",
    "summer": "summer",
    "winter": "winter",
}
SEMESTER_MONTHS = {
    "winter": {1, 2},
    "spring": {2, 3, 4, 5, 6},
    "summer": {6, 7, 8},
    "fall": {8, 9, 10, 11, 12},
}


def _normalize(value: str) -> str:
    cleaned = re.sub(r"[^\w\s]", " ", value.lower().strip())
    return " ".join(cleaned.split())


def _tokens(value: str) -> set[str]:
    return {token for token in _normalize(value).split() if token}


def _similarity(left: str, right: str) -> float:
    return SequenceMatcher(None, _normalize(left), _normalize(right)).ratio()


def _token_overlap(left: str, right: str) -> float:
    left_tokens = _tokens(left)
    right_tokens = _tokens(right)
    if not left_tokens or not right_tokens:
        return 0.0
    return len(left_tokens & right_tokens) / max(len(left_tokens), len(right_tokens))


def _matches(expected: str, actual: str, threshold: float = 0.82) -> bool:
    expected_norm = _normalize(expected)
    actual_norm = _normalize(actual)
    if not expected_norm or not actual_norm:
        return False
    if expected_norm == actual_norm:
        return True
    if expected_norm in actual_norm or actual_norm in expected_norm:
        return True
    if _token_overlap(expected, actual) >= threshold:
        return True
    return _similarity(expected, actual) >= threshold


def _has_supported_file_type(document: ScheduleDocument) -> bool:
    mime_type = _normalize(document.mimeType or "")
    if mime_type in SUPPORTED_MIME_TYPES:
        return True

    file_name = (document.fileName or document.filePath or document.fileUrl or "").strip().lower()
    return file_name.endswith(SUPPORTED_EXTENSIONS)


def _extract_semester_term(value: str) -> str:
    normalized = _normalize(value)
    for keyword, canonical in SEMESTER_KEYWORDS.items():
        if keyword in normalized:
            return canonical
    return ""


def _extract_semester_year(value: str) -> int | None:
    match = re.search(r"\b(20\d{2})\b", value)
    if not match:
        return None
    return int(match.group(1))


def _is_current_semester(document: ScheduleDocument, now: datetime | None = None) -> bool:
    if now is None:
        now = datetime.now(UTC)

    term = _extract_semester_term(document.semester)
    year = _extract_semester_year(document.semester)

    if term and year:
        if year != now.year:
            return False
        return now.month in SEMESTER_MONTHS.get(term, set())

    return document.isCurrentSemester


def _name_matches(expected: ExpectedStudent, document: ScheduleDocument) -> bool:
    has_expected_name = bool(_normalize(expected.fullName))
    has_document_name = bool(_normalize(document.studentName))
    if not has_expected_name or not has_document_name:
        return True
    return _matches(expected.fullName, document.studentName, threshold=0.78)


def _university_matches(expected: ExpectedStudent, document: ScheduleDocument) -> bool:
    return _matches(expected.university, document.university, threshold=0.72)


def verify_schedule(document: ScheduleDocument, expected: ExpectedStudent) -> ScheduleVerification:
    name_matches = _name_matches(expected, document)
    university_matches = _university_matches(expected, document)
    courses_present = len([course for course in document.courses if course.strip()]) > 0
    supported_file_type = _has_supported_file_type(document)
    semester_is_current = _is_current_semester(document)

    checks = {
        "supportedFileType": supported_file_type,
        "documentLooksLikeSchedule": document.documentLooksLikeSchedule,
        "nameMatchesExpected": name_matches,
        "universityMatchesExpected": university_matches,
        "semesterIsCurrent": semester_is_current,
        "coursesPresent": courses_present,
    }

    issues = [label for label, passed in checks.items() if not passed]
    passed_count = sum(1 for passed in checks.values() if passed)
    confidence = round(passed_count / len(checks), 2)
    is_verified = passed_count == len(checks)

    return ScheduleVerification(
        isVerified=is_verified,
        confidence=confidence,
        message=(
            "Schedule verified successfully."
            if is_verified
            else "Schedule could not be fully verified."
        ),
        extracted={
            "studentName": document.studentName,
            "university": document.university,
            "semester": document.semester,
            "courses": document.courses,
            "filePath": document.filePath,
            "fileUrl": document.fileUrl,
            "fileName": document.fileName,
            "mimeType": document.mimeType,
        },
        checks=checks,
        issues=issues,
    )
