from __future__ import annotations

import json
import mimetypes
import re
from pathlib import Path
from typing import Any

from api_server.remote_files import resolve_local_or_remote_path
from api_server.settings import settings
from transcript_verification.application.dtos import TranscriptDocumentPayload
from transcript_verification.infrastructure.azure_transcript_extractor import (
    build_azure_transcript_extractor,
)
from transcript_verification.infrastructure.local_transcript_extractor import (
    LocalTranscriptExtractor,
)


SUPPORTED_MIME_TYPES = {
    "application/pdf",
    "image/png",
    "image/jpeg",
    "image/webp",
}


class GeminiTranscriptExtractor:
    def __init__(self, api_key: str, model: str, timeout_seconds: int) -> None:
        self._api_key = api_key
        self._model = model
        self._timeout_seconds = timeout_seconds

    def extract(self, payload: TranscriptDocumentPayload) -> TranscriptDocumentPayload:
        file_path = _resolve_file_path(payload)
        mime_type = _detect_mime_type(payload, file_path)

        if mime_type not in SUPPORTED_MIME_TYPES:
            raise ValueError("transcript file must be PDF, PNG, JPEG, or WEBP")

        extracted = self._extract_with_gemini(file_path.read_bytes(), mime_type)

        return TranscriptDocumentPayload(
            filePath=str(file_path),
            fileUrl=payload.fileUrl,
            fileName=payload.fileName or file_path.name,
            mimeType=mime_type,
            documentLooksLikeTranscript=bool(extracted.get("documentLooksLikeTranscript")),
            documentType=str(extracted.get("documentType") or ""),
            studentName=str(extracted.get("studentName") or ""),
            university=str(extracted.get("university") or ""),
            degree=str(extracted.get("degree") or ""),
            major=str(extracted.get("major") or ""),
            gpa=_safe_float(extracted.get("gpa")),
            lastSemester=str(extracted.get("lastSemester") or ""),
            academicYear=str(extracted.get("academicYear") or ""),
            dateOfBirth=str(extracted.get("dateOfBirth") or ""),
            studentNumber=str(extracted.get("studentNumber") or ""),
            faculty=str(extracted.get("faculty") or ""),
            issuer=str(extracted.get("issuer") or ""),
            issueDate=str(extracted.get("issueDate") or ""),
            referenceNumber=str(extracted.get("referenceNumber") or ""),
            courses=[str(item).strip() for item in extracted.get("courses", []) if str(item).strip()],
            hasVerificationUrl=bool(extracted.get("hasVerificationUrl")),
            hasDigitalSignature=bool(extracted.get("hasDigitalSignature")),
            hasSignatureMarker=bool(extracted.get("hasSignatureMarker")),
        )

    def _extract_with_gemini(self, data: bytes, mime_type: str) -> dict[str, Any]:
        try:
            from google import genai
            from google.genai import types
        except ImportError as exc:
            raise ValueError("google-genai is required for transcript extraction") from exc

        client = genai.Client(api_key=self._api_key)
        prompt = (
            "Extract official university transcript or attestation fields from this file. "
            "The file may be in Arabic, English, or mixed. Return ONLY valid JSON with this exact shape: "
            "{"
            "\"documentLooksLikeTranscript\": boolean, "
            "\"documentType\": string, "
            "\"studentName\": string, "
            "\"university\": string, "
            "\"degree\": string, "
            "\"major\": string, "
            "\"gpa\": number|null, "
            "\"lastSemester\": string, "
            "\"academicYear\": string, "
            "\"dateOfBirth\": string, "
            "\"studentNumber\": string, "
            "\"faculty\": string, "
            "\"issuer\": string, "
            "\"issueDate\": string, "
            "\"referenceNumber\": string, "
            "\"courses\": string[], "
            "\"hasVerificationUrl\": boolean, "
            "\"hasDigitalSignature\": boolean, "
            "\"hasSignatureMarker\": boolean"
            "}. "
            "Rules: documentType must be one of transcript, attestation, certificate, or empty string. "
            "Do not invent data. Use empty string for unknown strings, [] for missing arrays, and null for missing GPA. "
            "For attestation documents, capture studentName, university, academicYear, faculty, issuer, issueDate, "
            "referenceNumber, studentNumber, dateOfBirth, and signature marker whenever visible."
        )

        try:
            response = client.models.generate_content(
                model=self._model,
                contents=[
                    types.Part.from_bytes(data=data, mime_type=mime_type),
                    prompt,
                ],
                config={
                    "response_mime_type": "application/json",
                    "temperature": settings.llm_temperature,
                    "max_output_tokens": max(settings.llm_max_output_tokens, 1024),
                    "http_options": {"timeout": self._timeout_seconds * 1000},
                },
            )
        except Exception as exc:
            raise ValueError(
                f"Gemini transcript extraction failed: {type(exc).__name__}: {exc}"
            ) from exc

        parsed = None
        for candidate_text in _extract_response_text_candidates(response):
            try:
                parsed = _parse_json_object(candidate_text)
                break
            except ValueError:
                continue

        if parsed is None or not isinstance(parsed, dict):
            raise ValueError("Gemini returned invalid transcript extraction JSON")
        return parsed


class CompositeTranscriptExtractor:
    def __init__(
        self,
        primary: Any,
        fallback: GeminiTranscriptExtractor | None = None,
    ) -> None:
        self._primary = primary
        self._fallback = fallback

    def extract(self, payload: TranscriptDocumentPayload) -> TranscriptDocumentPayload:
        local = self._primary.extract(payload)
        if self._fallback is None:
            return local
        if _looks_complete(local):
            return local
        try:
            gemini = self._fallback.extract(payload)
            if _looks_complete(gemini):
                return gemini
        except ValueError:
            pass
        return local


def build_gemini_transcript_extractor() -> GeminiTranscriptExtractor | None:
    if settings.llm_provider != "gemini" or not settings.gemini_api_key:
        return None
    return GeminiTranscriptExtractor(
        api_key=settings.gemini_api_key,
        model=settings.gemini_model,
        timeout_seconds=settings.llm_timeout_seconds,
    )


def build_transcript_extractor() -> CompositeTranscriptExtractor:
    return CompositeTranscriptExtractor(
        primary=build_azure_transcript_extractor() or LocalTranscriptExtractor(),
        fallback=build_gemini_transcript_extractor(),
    )


def _looks_complete(document: TranscriptDocumentPayload) -> bool:
    return bool(
        document.documentLooksLikeTranscript
        and document.documentType
        and document.studentName
        and document.university
        and (
            document.studentNumber
            or document.dateOfBirth
            or document.academicYear
            or document.issuer
        )
    )


def _resolve_file_path(payload: TranscriptDocumentPayload) -> Path:
    source = payload.filePath or payload.fileUrl
    if not source:
        raise ValueError("transcript filePath or fileUrl is required for extraction")
    try:
        return resolve_local_or_remote_path(source, prefix="jobloom-transcript-")
    except ValueError as exc:
        raise ValueError(f"transcript file not found: {source}") from exc


def _detect_mime_type(payload: TranscriptDocumentPayload, file_path: Path) -> str:
    if payload.mimeType:
        return payload.mimeType.lower().strip()
    guessed, _ = mimetypes.guess_type(file_path.name)
    if guessed:
        return guessed.lower()
    suffix = file_path.suffix.lower()
    if suffix == ".pdf":
        return "application/pdf"
    if suffix in {".jpg", ".jpeg"}:
        return "image/jpeg"
    if suffix == ".png":
        return "image/png"
    if suffix == ".webp":
        return "image/webp"
    return "application/octet-stream"


def _safe_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _parse_json_object(raw_text: str) -> dict[str, Any]:
    text = (raw_text or "").strip()
    if not text:
        raise ValueError("empty Gemini response")
    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass
    fenced = re.search(r"```(?:json)?\s*(\{[\s\S]*\})\s*```", text, re.IGNORECASE)
    if fenced:
        parsed = json.loads(fenced.group(1))
        if isinstance(parsed, dict):
            return parsed
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        parsed = json.loads(text[start : end + 1])
        if isinstance(parsed, dict):
            return parsed
    raise ValueError("no valid JSON object found in Gemini response")


def _extract_response_text_candidates(response: Any) -> list[str]:
    candidates: list[str] = []
    for attr_name in ("text", "raw_text"):
        attr = getattr(response, attr_name, None)
        if isinstance(attr, str) and attr.strip():
            candidates.append(attr)
    for method_name in ("model_dump", "to_dict"):
        method = getattr(response, method_name, None)
        if callable(method):
            try:
                dumped = method()
            except Exception:
                continue
            if isinstance(dumped, dict):
                candidates.extend(_collect_text_values(dumped))
    unique: list[str] = []
    seen: set[str] = set()
    for value in candidates:
        normalized = value.strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        unique.append(normalized)
    return unique


def _collect_text_values(obj: Any) -> list[str]:
    texts: list[str] = []
    if isinstance(obj, dict):
        for key, value in obj.items():
            if key in {"text", "output_text"} and isinstance(value, str) and value.strip():
                texts.append(value)
            texts.extend(_collect_text_values(value))
    elif isinstance(obj, list):
        for item in obj:
            texts.extend(_collect_text_values(item))
    return texts
