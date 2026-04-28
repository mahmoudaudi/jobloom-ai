from __future__ import annotations

import base64
import json
import mimetypes
import re
from pathlib import Path
from typing import Any

from api_server.settings import settings
from schedule_verification.application.dtos import ScheduleDocumentPayload
from schedule_verification.infrastructure.local_schedule_extractor import (
    CompositeScheduleExtractor,
    LocalScheduleExtractor,
)


SUPPORTED_MIME_TYPES = {
    "application/pdf",
    "image/png",
    "image/jpeg",
    "image/webp",
}


class GeminiScheduleExtractor:
    def __init__(self, api_key: str, model: str, timeout_seconds: int) -> None:
        self._api_key = api_key
        self._model = model
        self._timeout_seconds = timeout_seconds

    def extract(self, payload: ScheduleDocumentPayload) -> ScheduleDocumentPayload:
        file_path = _resolve_file_path(payload)
        data = file_path.read_bytes()
        mime_type = _detect_mime_type(payload, file_path)

        if mime_type not in SUPPORTED_MIME_TYPES:
            raise ValueError("schedule file must be PDF, PNG, JPEG, or WEBP")

        extracted = self._extract_with_gemini(data, mime_type)

        return ScheduleDocumentPayload(
            filePath=str(file_path),
            fileUrl=payload.fileUrl,
            fileName=payload.fileName or file_path.name,
            mimeType=mime_type,
            documentLooksLikeSchedule=bool(extracted.get("documentLooksLikeSchedule")),
            studentName=str(extracted.get("studentName") or ""),
            university=str(extracted.get("university") or ""),
            semester=str(extracted.get("semester") or ""),
            isCurrentSemester=bool(extracted.get("isCurrentSemester")),
            courses=[
                str(course).strip()
                for course in extracted.get("courses", [])
                if str(course).strip()
            ],
            locations=[
                str(location).strip()
                for location in extracted.get("locations", [])
                if str(location).strip()
            ],
        )

    def classify_document(self, payload: ScheduleDocumentPayload) -> dict[str, Any]:
        file_path = _resolve_file_path(payload)
        data = file_path.read_bytes()
        mime_type = _detect_mime_type(payload, file_path)

        if mime_type not in SUPPORTED_MIME_TYPES:
            raise ValueError("schedule file must be PDF, PNG, JPEG, or WEBP")

        try:
            from google import genai
            from google.genai import types
        except ImportError as exc:
            raise ValueError("google-genai is required for schedule classification") from exc

        client = genai.Client(api_key=self._api_key)
        prompt = (
            "Classify whether this document is a university class schedule/timetable."
            " It may be in Arabic or English. "
            "Return ONLY JSON with this exact shape: "
            "{"
            "\"isSchedule\": boolean, "
            "\"confidence\": number, "
            "\"reason\": string"
            "}. "
            "Use confidence from 0.0 to 1.0. "
            "A class schedule usually includes course list and/or time table, term/semester references, "
            "and university/student enrollment context."
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
                    "temperature": 0.0,
                    "max_output_tokens": 256,
                    "http_options": {"timeout": self._timeout_seconds * 1000},
                },
            )
        except Exception as exc:
            raise ValueError(
                f"Gemini schedule classification failed: {type(exc).__name__}: {exc}"
            ) from exc

        parsed = None
        parse_errors: list[str] = []
        for candidate_text in _extract_response_text_candidates(response):
            try:
                parsed = _parse_json_object(candidate_text)
                break
            except ValueError as exc:
                parse_errors.append(str(exc))

        if parsed is None:
            preview = _response_preview(response)
            details = "; ".join(parse_errors) if parse_errors else "no parse attempts"
            raise ValueError(
                "Gemini returned invalid schedule classification JSON "
                f"(details: {details}; preview: {preview})"
            )

        is_schedule = bool(parsed.get("isSchedule"))
        confidence_raw = parsed.get("confidence", 1.0 if is_schedule else 0.0)
        try:
            confidence = float(confidence_raw)
        except (TypeError, ValueError):
            confidence = 1.0 if is_schedule else 0.0
        confidence = max(0.0, min(1.0, confidence))
        reason = str(parsed.get("reason") or "").strip()

        return {
            "isSchedule": is_schedule,
            "confidence": confidence,
            "reason": reason,
        }

    def _extract_with_gemini(self, data: bytes, mime_type: str) -> dict[str, Any]:
        try:
            from google import genai
            from google.genai import types
        except ImportError as exc:
            raise ValueError("google-genai is required for real schedule extraction") from exc

        client = genai.Client(api_key=self._api_key)
        prompt = (
            "Extract university class schedule information from this file. "
            "The file may be a PDF or an image. Return only JSON with this exact shape: "
            "{"
            "\"documentLooksLikeSchedule\": boolean, "
            "\"studentName\": string, "
            "\"university\": string, "
            "\"semester\": string, "
            "\"isCurrentSemester\": boolean, "
            "\"courses\": string[], "
            "\"locations\": string[]"
            "}. "
            "Set unknown strings to empty string. Do not invent missing fields. "
            "courses should contain visible course codes only. "
            "locations should contain classroom or campus location strings only."
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
                    "max_output_tokens": settings.llm_max_output_tokens,
                    "http_options": {"timeout": self._timeout_seconds * 1000},
                },
            )
        except Exception as exc:
            raise ValueError(
                f"Gemini schedule extraction failed: {type(exc).__name__}: {exc}"
            ) from exc

        parsed = None
        parse_errors: list[str] = []
        for candidate_text in _extract_response_text_candidates(response):
            try:
                parsed = _parse_json_object(candidate_text)
                break
            except ValueError as exc:
                parse_errors.append(str(exc))

        if parsed is None:
            preview = _response_preview(response)
            details = "; ".join(parse_errors) if parse_errors else "no parse attempts"
            raise ValueError(
                "Gemini returned invalid schedule extraction JSON "
                f"(details: {details}; preview: {preview})"
            )

        if not isinstance(parsed, dict):
            raise ValueError("Gemini returned invalid schedule extraction shape")
        return parsed


def build_gemini_schedule_extractor() -> GeminiScheduleExtractor | None:
    if settings.llm_provider != "gemini" or not settings.gemini_api_key:
        return None
    return GeminiScheduleExtractor(
        api_key=settings.gemini_api_key,
        model=settings.gemini_model,
        timeout_seconds=settings.llm_timeout_seconds,
    )


def build_schedule_extractor() -> CompositeScheduleExtractor:
    return CompositeScheduleExtractor(
        primary=LocalScheduleExtractor(),
        fallback=build_gemini_schedule_extractor(),
    )


def _resolve_file_path(payload: ScheduleDocumentPayload) -> Path:
    source = payload.filePath or payload.fileUrl
    if not source:
        raise ValueError("schedule filePath or fileUrl is required for extraction")

    path = Path(source)
    if not path.is_absolute():
        path = Path.cwd() / source.lstrip("/\\")

    if not path.exists() or not path.is_file():
        raise ValueError(f"schedule file not found: {path}")

    return path


def _detect_mime_type(payload: ScheduleDocumentPayload, file_path: Path) -> str:
    if payload.mimeType:
        return payload.mimeType.lower().strip()

    guessed, _encoding = mimetypes.guess_type(file_path.name)
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

    raw = base64.b16encode(file_path.read_bytes()[:8]).decode("ascii")
    if raw.startswith("25504446"):
        return "application/pdf"
    if raw.startswith("89504E47"):
        return "image/png"
    if raw.startswith("FFD8FF"):
        return "image/jpeg"
    if raw.startswith("52494646"):
        return "image/webp"

    return "application/octet-stream"


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
        try:
            parsed = json.loads(fenced.group(1))
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass

    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        candidate = text[start : end + 1]
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass

    raise ValueError("no valid JSON object found in Gemini response")


def _extract_response_text_candidates(response: Any) -> list[str]:
    candidates: list[str] = []

    text_attr = getattr(response, "text", None)
    if isinstance(text_attr, str) and text_attr.strip():
        candidates.append(text_attr)

    raw_text_attr = getattr(response, "raw_text", None)
    if isinstance(raw_text_attr, str) and raw_text_attr.strip():
        candidates.append(raw_text_attr)

    response_dict: dict[str, Any] | None = None

    model_dump = getattr(response, "model_dump", None)
    if callable(model_dump):
        try:
            dumped = model_dump()
            if isinstance(dumped, dict):
                response_dict = dumped
                candidates.extend(_collect_text_values(dumped))
        except Exception:
            pass

    model_dump_json = getattr(response, "model_dump_json", None)
    if callable(model_dump_json):
        try:
            dumped_json = model_dump_json()
            if isinstance(dumped_json, str) and dumped_json.strip():
                candidates.append(dumped_json)
        except Exception:
            pass

    if response_dict is None:
        to_dict = getattr(response, "to_dict", None)
        if callable(to_dict):
            try:
                dumped = to_dict()
                if isinstance(dumped, dict):
                    response_dict = dumped
                    candidates.extend(_collect_text_values(dumped))
            except Exception:
                pass

    if response_dict is None:
        candidates_attr = getattr(response, "candidates", None)
        if isinstance(candidates_attr, list):
            candidates.extend(_collect_text_values({"candidates": candidates_attr}))

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
            if key in {"text", "output_text"} and isinstance(value, str):
                if value.strip():
                    texts.append(value)
            texts.extend(_collect_text_values(value))
    elif isinstance(obj, list):
        for item in obj:
            texts.extend(_collect_text_values(item))
    return texts


def _response_preview(response: Any, max_len: int = 240) -> str:
    parts: list[str] = []
    text_attr = getattr(response, "text", None)
    if isinstance(text_attr, str) and text_attr.strip():
        parts.append(text_attr.strip())

    as_string = str(response)
    if as_string.strip():
        parts.append(as_string.strip())

    preview = " | ".join(parts).replace("\n", " ").strip()
    if len(preview) > max_len:
        return preview[: max_len - 3] + "..."
    return preview or "<empty>"
