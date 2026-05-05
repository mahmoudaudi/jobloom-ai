from __future__ import annotations

import re
from difflib import SequenceMatcher

from .models import ExpectedStudent, TranscriptDocument, TranscriptVerification


SUPPORTED_EXTENSIONS = (".pdf", ".png", ".jpg", ".jpeg", ".webp")
SUPPORTED_MIME_TYPES = ("application/pdf", "image/png", "image/jpeg", "image/webp")


def _normalize(value: str) -> str:
    cleaned = re.sub(r"[^\w\s]", " ", value.lower().strip())
    return " ".join(cleaned.split())


def _similarity(left: str, right: str) -> float:
    return SequenceMatcher(None, _normalize(left), _normalize(right)).ratio()


def _matches(expected: str, actual: str, threshold: float = 0.78) -> bool:
    expected_norm = _normalize(expected)
    actual_norm = _normalize(actual)
    if not expected_norm or not actual_norm:
        return False
    if expected_norm == actual_norm:
        return True
    if expected_norm in actual_norm or actual_norm in expected_norm:
        return True
    return _similarity(expected, actual) >= threshold


def _year_matches(expected: str, actual: str) -> bool:
    expected_norm = _normalize(expected)
    actual_norm = _normalize(actual)
    if not expected_norm or not actual_norm:
        return False
    if expected_norm == actual_norm:
        return True
    expected_digits = re.findall(r"20\d{2}", expected)
    actual_digits = re.findall(r"20\d{2}", actual)
    return bool(expected_digits and actual_digits and expected_digits == actual_digits)


def _has_supported_file_type(document: TranscriptDocument) -> bool:
    mime_type = _normalize(document.mimeType or "")
    if mime_type in SUPPORTED_MIME_TYPES:
        return True
    file_name = (document.fileName or document.filePath or document.fileUrl or "").strip().lower()
    return file_name.endswith(SUPPORTED_EXTENSIONS)


def verify_transcript(
    document: TranscriptDocument,
    expected: ExpectedStudent,
) -> TranscriptVerification:
    supported_file_type = _has_supported_file_type(document)
    name_matches = True if not expected.fullName or not document.studentName else _matches(expected.fullName, document.studentName)
    university_matches = _matches(expected.university, document.university, threshold=0.72)
    major_matches = True if not expected.major or not document.major else _matches(expected.major, document.major, threshold=0.72)
    date_of_birth_matches = True if not expected.dateOfBirth or not document.dateOfBirth else _matches(expected.dateOfBirth, document.dateOfBirth, threshold=0.72)
    academic_year_matches = True if not expected.academicYear or not document.academicYear else _year_matches(expected.academicYear, document.academicYear)
    records_present = bool(document.gpa is not None or document.courses)
    recent_activity_present = bool(document.lastSemester.strip())
    identity_present = bool(document.studentNumber.strip() or document.dateOfBirth.strip())
    issuer_present = bool(document.issuer.strip())
    issue_date_present = bool(document.issueDate.strip())
    reference_number_present = bool(document.referenceNumber.strip())
    faculty_present = bool(document.faculty.strip())
    signature_present = document.hasSignatureMarker or document.hasDigitalSignature
    strong_proof_present = document.hasVerificationUrl or document.hasDigitalSignature
    document_type_supported = document.documentType in {"transcript", "attestation", "certificate"} if document.documentType else document.documentLooksLikeTranscript

    checks = {
        "supportedFileType": supported_file_type,
        "documentLooksLikeTranscript": document.documentLooksLikeTranscript,
        "documentTypeSupported": document_type_supported,
        "nameMatchesExpected": name_matches,
        "universityMatchesExpected": university_matches,
        "majorMatchesExpected": major_matches,
        "dateOfBirthMatchesExpected": date_of_birth_matches,
        "academicYearMatchesExpected": academic_year_matches,
        "recordsPresent": records_present,
        "recentAcademicActivity": recent_activity_present,
        "identitySignalPresent": identity_present,
        "facultyPresent": faculty_present,
        "issuerPresent": issuer_present,
        "issueDatePresent": issue_date_present,
        "referenceNumberPresent": reference_number_present,
        "signaturePresent": signature_present,
        "strongProofPresent": strong_proof_present,
    }

    required_checks = {
        "supportedFileType": supported_file_type,
        "documentLooksLikeTranscript": document.documentLooksLikeTranscript,
        "documentTypeSupported": document_type_supported,
        "nameMatchesExpected": name_matches,
        "universityMatchesExpected": university_matches,
        "majorMatchesExpected": major_matches,
        "identitySignalPresent": identity_present,
    }

    issues = [label for label, passed in checks.items() if not passed]
    passed_count = sum(1 for passed in checks.values() if passed)
    confidence = round(passed_count / len(checks), 2)
    is_verified = strong_proof_present or all(required_checks.values())

    return TranscriptVerification(
        isVerified=is_verified,
        confidence=confidence,
        message=(
            "Transcript verified successfully."
            if is_verified
            else "Transcript could not be fully verified."
        ),
        extracted={
            "studentName": document.studentName,
            "documentType": document.documentType,
            "university": document.university,
            "degree": document.degree,
            "major": document.major,
            "gpa": document.gpa,
            "lastSemester": document.lastSemester,
            "academicYear": document.academicYear,
            "dateOfBirth": document.dateOfBirth,
            "studentNumber": document.studentNumber,
            "faculty": document.faculty,
            "issuer": document.issuer,
            "issueDate": document.issueDate,
            "referenceNumber": document.referenceNumber,
            "courses": document.courses,
            "filePath": document.filePath,
            "fileUrl": document.fileUrl,
            "fileName": document.fileName,
            "mimeType": document.mimeType,
        },
        checks=checks,
        issues=issues,
    )
