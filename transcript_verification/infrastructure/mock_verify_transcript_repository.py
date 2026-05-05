from __future__ import annotations

from transcript_verification.domain.models import ExpectedStudent, TranscriptDocument

from .mock_fixture import load_fixture


class MockVerifyTranscriptRepository:
    def get_mock_expected_student(self) -> ExpectedStudent:
        raw = load_fixture()["expected"]
        return ExpectedStudent(
            fullName=raw.get("fullName", ""),
            university=raw.get("university", ""),
            major=raw.get("major", ""),
            dateOfBirth=raw.get("dateOfBirth", ""),
            academicYear=raw.get("academicYear", ""),
        )

    def get_mock_transcript_document(self) -> TranscriptDocument:
        raw = load_fixture()["transcript"]
        return TranscriptDocument(
            filePath=raw.get("filePath"),
            fileUrl=raw.get("fileUrl"),
            fileName=raw.get("fileName"),
            mimeType=raw.get("mimeType"),
            documentLooksLikeTranscript=bool(raw.get("documentLooksLikeTranscript")),
            documentType=raw.get("documentType", ""),
            studentName=raw.get("studentName", ""),
            university=raw.get("university", ""),
            degree=raw.get("degree", ""),
            major=raw.get("major", ""),
            gpa=raw.get("gpa"),
            lastSemester=raw.get("lastSemester", ""),
            academicYear=raw.get("academicYear", ""),
            dateOfBirth=raw.get("dateOfBirth", ""),
            studentNumber=raw.get("studentNumber", ""),
            faculty=raw.get("faculty", ""),
            issuer=raw.get("issuer", ""),
            issueDate=raw.get("issueDate", ""),
            referenceNumber=raw.get("referenceNumber", ""),
            courses=list(raw.get("courses", [])),
            hasVerificationUrl=bool(raw.get("hasVerificationUrl")),
            hasDigitalSignature=bool(raw.get("hasDigitalSignature")),
            hasSignatureMarker=bool(raw.get("hasSignatureMarker")),
        )
