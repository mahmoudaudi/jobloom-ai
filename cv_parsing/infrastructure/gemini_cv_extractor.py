from __future__ import annotations

import mimetypes
import json
import re
import time
from pathlib import Path
from typing import Any

from api_server.settings import settings
from cv_parsing.application.dtos import ParseCvRequest
from cv_parsing.domain.models import (
    ConfidenceInfo,
    EducationInfo,
    ExperienceInfo,
    ParsedCv,
    PersonalInfo,
)
from cv_parsing.infrastructure.local_cv_extractor import LocalCvExtractor


class GeminiCvExtractor:
    def __init__(self, api_key: str, model: str, timeout_seconds: int) -> None:
        self._api_key = api_key
        self._model = model
        self._timeout_seconds = timeout_seconds

    def extract(self, payload: ParseCvRequest, raw_text: str | None = None) -> ParsedCv:
        text = (raw_text or "").strip()
        parsed = None
        file_source = payload.filePath or payload.fileUrl

        if file_source:
            file_path = _resolve_file_path(file_source)
            mime_type = _detect_mime_type(payload, file_path)
            try:
                parsed = self._extract_with_gemini_file(file_path, mime_type)
            except ValueError:
                parsed = None

        if parsed is None:
            if not text:
                raise ValueError("cv text is required for Gemini parsing")
            parsed = self._extract_with_gemini_text(text)

        personal_raw = parsed.get("personal", {}) if isinstance(parsed.get("personal"), dict) else {}
        education_raw = parsed.get("education", {}) if isinstance(parsed.get("education"), dict) else {}
        confidence_raw = parsed.get("confidence", {}) if isinstance(parsed.get("confidence"), dict) else {}

        experiences: list[ExperienceInfo] = []
        for item in parsed.get("experiences", []):
            if not isinstance(item, dict):
                continue
            experiences.append(
                ExperienceInfo(
                    title=str(item.get("title") or "").strip(),
                    company=str(item.get("company") or "").strip(),
                    period=str(item.get("period") or "").strip(),
                    description=str(item.get("description") or "").strip(),
                )
            )

        skills = _normalize_skills(parsed.get("skills", []))
        language = str(parsed.get("language") or ("ar" if re.search(r"[\u0600-\u06FF]", text) else "en"))

        return ParsedCv(
            personal=PersonalInfo(
                fullName=str(personal_raw.get("fullName") or "").strip(),
                email=str(personal_raw.get("email") or "").strip(),
                phone=_normalize_phone(str(personal_raw.get("phone") or "").strip()),
                country=str(personal_raw.get("country") or "").strip(),
                city=str(personal_raw.get("city") or "").strip(),
            ),
            education=EducationInfo(
                degree=str(education_raw.get("degree") or "").strip(),
                majorName=str(education_raw.get("majorName") or "").strip(),
                university=str(education_raw.get("university") or "").strip(),
                yearLabel=str(education_raw.get("yearLabel") or "").strip(),
                educationPeriod=str(education_raw.get("educationPeriod") or "").strip(),
                expectedGraduation=str(education_raw.get("expectedGraduation") or "").strip(),
                gpa=_safe_float(education_raw.get("gpa")),
            ),
            skills=skills,
            experiences=experiences,
            confidence=ConfidenceInfo(
                overall=_bounded_float(confidence_raw.get("overall")),
                personal=_bounded_float(confidence_raw.get("personal")),
                education=_bounded_float(confidence_raw.get("education")),
                skills=_bounded_float(confidence_raw.get("skills")),
                experiences=_bounded_float(confidence_raw.get("experiences")),
            ),
            rawText=text[:4000],
            language=language,
        )

    def _extract_with_gemini_file(self, file_path: Path, mime_type: str) -> dict[str, Any]:
        try:
            from google import genai
            from google.genai import types
        except ImportError as exc:
            raise ValueError("google-genai is required for Gemini CV parsing") from exc

        client = genai.Client(api_key=self._api_key)
        prompt = (
            "You are a CV parser. Read the attached CV file and extract structured student profile data. "
            "Return ONLY valid JSON with this exact shape: "
            "{"
            "\"personal\": {\"fullName\": string, \"email\": string, \"phone\": string, \"country\": string, \"city\": string}, "
            "\"education\": {\"degree\": string, \"majorName\": string, \"university\": string, \"yearLabel\": string, "
            "\"educationPeriod\": string, \"expectedGraduation\": string, \"gpa\": number|null}, "
            "\"skills\": string[], "
            "\"experiences\": [{\"title\": string, \"company\": string, \"period\": string, \"description\": string}], "
            "\"confidence\": {\"overall\": number, \"personal\": number, \"education\": number, \"skills\": number, \"experiences\": number}, "
            "\"language\": string"
            "}. "
            "Rules: never invent missing data, use empty string for unknown strings, use [] for missing arrays, use null for missing GPA. "
            "Skills must be deduplicated and clean. Experiences must describe only what is present in the file. "
            "The CV may be in English or Arabic."
        )

        response = self._generate_with_retry(
            client,
            contents=[
                types.Part.from_bytes(data=file_path.read_bytes(), mime_type=mime_type),
                prompt,
            ],
        )

        return self._parse_response(response)

    def _extract_with_gemini_text(self, text: str) -> dict[str, Any]:
        try:
            from google import genai
        except ImportError as exc:
            raise ValueError("google-genai is required for Gemini CV parsing") from exc

        client = genai.Client(api_key=self._api_key)
        prompt = (
            "You are a CV parser. Extract structured student profile data from the CV text below. "
            "Return ONLY valid JSON with this exact shape: "
            "{"
            "\"personal\": {\"fullName\": string, \"email\": string, \"phone\": string, \"country\": string, \"city\": string}, "
            "\"education\": {\"degree\": string, \"majorName\": string, \"university\": string, \"yearLabel\": string, "
            "\"educationPeriod\": string, \"expectedGraduation\": string, \"gpa\": number|null}, "
            "\"skills\": string[], "
            "\"experiences\": [{\"title\": string, \"company\": string, \"period\": string, \"description\": string}], "
            "\"confidence\": {\"overall\": number, \"personal\": number, \"education\": number, \"skills\": number, \"experiences\": number}, "
            "\"language\": string"
            "}. "
            "Rules: never invent missing data, use empty string for unknown strings, use [] for missing arrays, use null for missing GPA. "
            "Skills must be deduplicated and clean. Experiences must describe only what is present in the text. "
            "The CV may be in English or Arabic.\n\n"
            f"CV TEXT:\n\"\"\"\n{text}\n\"\"\""
        )

        response = self._generate_with_retry(client, contents=prompt)
        return self._parse_response(response)

    def _generate_with_retry(self, client: Any, contents: Any) -> Any:
        response = None
        last_error: Exception | None = None
        for attempt in range(3):
            try:
                response = client.models.generate_content(
                    model=self._model,
                    contents=contents,
                    config={
                        "response_mime_type": "application/json",
                        "temperature": settings.llm_temperature,
                        "max_output_tokens": max(settings.llm_max_output_tokens, 1024),
                        "http_options": {"timeout": self._timeout_seconds * 1000},
                    },
                )
                last_error = None
                break
            except Exception as exc:
                last_error = exc
                if "503" not in str(exc) and "UNAVAILABLE" not in str(exc):
                    break
                if attempt < 2:
                    time.sleep(attempt + 1)

        if response is None:
            assert last_error is not None
            raise ValueError(
                f"Gemini CV parsing failed: {type(last_error).__name__}: {last_error}"
            ) from last_error
        return response

    def _parse_response(self, response: Any) -> dict[str, Any]:
        
        parsed = None
        parse_errors: list[str] = []
        for candidate_text in _extract_response_text_candidates(response):
            try:
                parsed = _parse_json_object(candidate_text)
                break
            except ValueError as exc:
                parse_errors.append(str(exc))

        if parsed is None:
            details = "; ".join(parse_errors) if parse_errors else "no parse attempts"
            raise ValueError(f"Gemini returned invalid CV parsing JSON ({details})")
        if not isinstance(parsed, dict):
            raise ValueError("Gemini returned invalid CV parsing shape")
        return parsed


class CompositeCvExtractor:
    def __init__(self, primary: LocalCvExtractor, fallback: GeminiCvExtractor | None = None) -> None:
        self._primary = primary
        self._fallback = fallback

    def extract(self, payload: ParseCvRequest) -> ParsedCv:
        raw_text = self._primary.extract_text(payload)
        if self._fallback is not None:
            try:
                parsed = self._fallback.extract(payload, raw_text=raw_text)
                if _looks_complete(parsed):
                    return parsed
            except ValueError:
                pass
        return self._primary.parse_text(raw_text)


def build_gemini_cv_extractor() -> GeminiCvExtractor | None:
    if settings.llm_provider != "gemini" or not settings.gemini_api_key:
        return None
    return GeminiCvExtractor(
        api_key=settings.gemini_api_key,
        model=settings.gemini_model,
        timeout_seconds=settings.llm_timeout_seconds,
    )


def build_cv_extractor() -> CompositeCvExtractor:
    return CompositeCvExtractor(
        primary=LocalCvExtractor(),
        fallback=build_gemini_cv_extractor(),
    )


def _looks_complete(parsed: ParsedCv) -> bool:
    return bool(
        (parsed.personal.fullName or parsed.personal.email or parsed.personal.phone)
        and (parsed.education.university or parsed.education.majorName or parsed.education.degree)
        and (parsed.skills or parsed.experiences)
    )


def _normalize_skills(raw_skills: Any) -> list[str]:
    if not isinstance(raw_skills, list):
        return []
    skills: list[str] = []
    seen: set[str] = set()
    for item in raw_skills:
        cleaned = str(item or "").strip()
        if not cleaned:
            continue
        normalized = cleaned.lower()
        if normalized in seen:
            continue
        seen.add(normalized)
        skills.append(cleaned)
    return skills[:20]


def _normalize_phone(value: str) -> str:
    return re.sub(r"[^\d+]", "", value)


def _safe_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _bounded_float(value: Any) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        numeric = 0.0
    return max(0.0, min(1.0, numeric))


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


def _resolve_file_path(source: str) -> Path:
    path = Path(source)
    if not path.is_absolute():
        path = Path.cwd() / source.lstrip("/\\")
    if not path.exists() or not path.is_file():
        raise ValueError(f"cv file not found: {path}")
    return path


def _detect_mime_type(payload: ParseCvRequest, file_path: Path) -> str:
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
