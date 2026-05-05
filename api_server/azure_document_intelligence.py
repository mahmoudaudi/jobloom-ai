from __future__ import annotations

from pathlib import Path

from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.core.credentials import AzureKeyCredential
from api_server.text_cleaning import clean_extracted_text


class AzureDocumentIntelligenceExtractor:
    def __init__(self, endpoint: str, api_key: str, timeout_seconds: int) -> None:
        self._endpoint = endpoint
        self._api_key = api_key
        self._timeout_seconds = timeout_seconds
        self._client = DocumentIntelligenceClient(
            endpoint=endpoint,
            credential=AzureKeyCredential(api_key),
        )

    def extract_text(self, file_path: Path) -> str:
        with file_path.open("rb") as handle:
            poller = self._client.begin_analyze_document(
                "prebuilt-layout",
                body=handle,
                output_content_format="text",
            )
            result = poller.result(timeout=self._timeout_seconds)
        return clean_extracted_text((result.content or "").strip())
