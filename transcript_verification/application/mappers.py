from __future__ import annotations

from transcript_verification.domain.models import ExpectedStudent, TranscriptDocument

from .dtos import ExpectedStudentPayload, TranscriptDocumentPayload


def to_expected_student(payload: ExpectedStudentPayload | None) -> ExpectedStudent:
    if payload is None:
        return ExpectedStudent()
    return ExpectedStudent(
        fullName=payload.fullName,
        university=payload.university,
        major=payload.major,
    )


def to_transcript_document(payload: TranscriptDocumentPayload) -> TranscriptDocument:
    return TranscriptDocument(
        filePath=payload.filePath,
        fileUrl=payload.fileUrl,
        fileName=payload.fileName,
        mimeType=payload.mimeType,
        documentLooksLikeTranscript=payload.documentLooksLikeTranscript,
        studentName=payload.studentName,
        university=payload.university,
        degree=payload.degree,
        major=payload.major,
        gpa=payload.gpa,
        lastSemester=payload.lastSemester,
        courses=payload.courses,
        hasVerificationUrl=payload.hasVerificationUrl,
        hasDigitalSignature=payload.hasDigitalSignature,
    )

