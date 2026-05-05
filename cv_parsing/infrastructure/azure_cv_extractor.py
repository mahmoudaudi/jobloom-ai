from __future__ import annotations

from api_server.azure_document_intelligence import AzureDocumentIntelligenceExtractor
from api_server.settings import settings
from cv_parsing.application.dtos import ParseCvRequest
from cv_parsing.infrastructure.local_cv_extractor import (
    LocalCvExtractor,
    _resolve_file_path,
)


class AzureCvExtractor:
    def __init__(self, extractor: AzureDocumentIntelligenceExtractor) -> None:
        self._extractor = extractor
        self._fallback = LocalCvExtractor()

    def extract_text(self, payload: ParseCvRequest) -> str:
        file_path = _resolve_file_path(payload.filePath or payload.fileUrl or "")
        return self._extractor.extract_text(file_path)

    def parse_text(self, text: str):
        return self._fallback.parse_text(text)


def build_azure_cv_extractor() -> AzureCvExtractor | None:
    if (
        not settings.azure_document_intelligence_endpoint
        or not settings.azure_document_intelligence_key
    ):
        return None
    return AzureCvExtractor(
        AzureDocumentIntelligenceExtractor(
            settings.azure_document_intelligence_endpoint,
            settings.azure_document_intelligence_key,
            settings.llm_timeout_seconds,
        )
    )
