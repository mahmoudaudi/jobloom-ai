from __future__ import annotations

from api_server.azure_document_intelligence import AzureDocumentIntelligenceExtractor
from api_server.settings import settings
from transcript_verification.application.dtos import TranscriptDocumentPayload
from transcript_verification.infrastructure.local_transcript_extractor import (
    _detect_mime_type,
    _extract_transcript_fields,
    _has_pdf_signature,
    _resolve_file_path,
)


class AzureTranscriptExtractor:
    def __init__(self, extractor: AzureDocumentIntelligenceExtractor) -> None:
        self._extractor = extractor

    def extract(self, payload: TranscriptDocumentPayload) -> TranscriptDocumentPayload:
        file_path = _resolve_file_path(payload)
        mime_type = _detect_mime_type(payload, file_path)
        text = self._extractor.extract_text(file_path)
        fields = _extract_transcript_fields(text)

        return TranscriptDocumentPayload(
            filePath=str(file_path),
            fileUrl=payload.fileUrl,
            fileName=payload.fileName or file_path.name,
            mimeType=mime_type,
            documentLooksLikeTranscript=fields["documentLooksLikeTranscript"],
            documentType=fields["documentType"],
            studentName=fields["studentName"],
            university=fields["university"],
            degree=fields["degree"],
            major=fields["major"],
            gpa=fields["gpa"],
            lastSemester=fields["lastSemester"],
            academicYear=fields["academicYear"],
            dateOfBirth=fields["dateOfBirth"],
            studentNumber=fields["studentNumber"],
            faculty=fields["faculty"],
            issuer=fields["issuer"],
            issueDate=fields["issueDate"],
            referenceNumber=fields["referenceNumber"],
            courses=fields["courses"],
            hasVerificationUrl=fields["hasVerificationUrl"],
            hasDigitalSignature=_has_pdf_signature(file_path) if mime_type == "application/pdf" else False,
            hasSignatureMarker=fields["hasSignatureMarker"],
        )


def build_azure_transcript_extractor() -> AzureTranscriptExtractor | None:
    if (
        not settings.azure_document_intelligence_endpoint
        or not settings.azure_document_intelligence_key
    ):
        return None
    return AzureTranscriptExtractor(
        AzureDocumentIntelligenceExtractor(
            settings.azure_document_intelligence_endpoint,
            settings.azure_document_intelligence_key,
            settings.llm_timeout_seconds,
        )
    )
