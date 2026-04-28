from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from schedule_verification.application.dtos import ScheduleDocumentPayload


SUPPORTED_MIME_TYPES = {
    "application/pdf",
    "image/png",
    "image/jpeg",
    "image/webp",
}
SCHEDULE_KEYWORDS = (
    "schedule",
    "timetable",
    "semester",
    "courses",
    "course",
    "student",
    "university",
    "الجدول",
    "الفصل",
    "المقررات",
    "المواد",
    "الجامعة",
)
COURSE_LINE_PATTERN = re.compile(r"\b[A-Z]{2,}\s*[-/]?\s*\d{2,3}[A-Z]?\b")
SEMESTER_PATTERN = re.compile(
    r"\b(Spring|Summer|Fall|Winter|Autumn)\s+20\d{2}\b|\b20\d{2}\s+(Spring|Summer|Fall|Winter|Autumn)\b",
    re.IGNORECASE,
)
ARABIC_SEMESTER_PATTERN = re.compile(r"(20\d{2}).{0,20}(الفصل|الترم)", re.IGNORECASE)


class LocalScheduleExtractor:
    def extract(self, payload: ScheduleDocumentPayload) -> ScheduleDocumentPayload:
        file_path = _resolve_file_path(payload)
        mime_type = _detect_mime_type(payload, file_path)

        if mime_type not in SUPPORTED_MIME_TYPES:
            raise ValueError("schedule file must be PDF, PNG, JPEG, or WEBP")

        text = _extract_document_text(file_path, mime_type)
        extracted = _extract_schedule_fields(text)

        return ScheduleDocumentPayload(
            filePath=str(file_path),
            fileUrl=payload.fileUrl,
            fileName=payload.fileName or file_path.name,
            mimeType=mime_type,
            documentLooksLikeSchedule=extracted["documentLooksLikeSchedule"],
            studentName=extracted["studentName"],
            university=extracted["university"],
            semester=extracted["semester"],
            isCurrentSemester=extracted["isCurrentSemester"],
            courses=extracted["courses"],
        )

    def classify_document(self, payload: ScheduleDocumentPayload) -> dict[str, Any]:
        extracted = self.extract(payload)
        return {
            "isSchedule": extracted.documentLooksLikeSchedule,
            "confidence": _classification_confidence(extracted),
            "reason": (
                "Detected schedule keywords, semester data, and course lines."
                if extracted.documentLooksLikeSchedule
                else "Could not find enough schedule-specific signals in the document."
            ),
        }


class CompositeScheduleExtractor:
    def __init__(self, primary: LocalScheduleExtractor, fallback: Any | None = None) -> None:
        self._primary = primary
        self._fallback = fallback

    def extract(self, payload: ScheduleDocumentPayload) -> ScheduleDocumentPayload:
        primary_result = self._primary.extract(payload)
        if _looks_complete(primary_result):
            return primary_result
        if self._fallback is None:
            return primary_result
        return self._fallback.extract(payload)

    def classify_document(self, payload: ScheduleDocumentPayload) -> dict[str, Any]:
        classification = self._primary.classify_document(payload)
        if classification["isSchedule"] or self._fallback is None:
            return classification
        return self._fallback.classify_document(payload)


def _looks_complete(payload: ScheduleDocumentPayload) -> bool:
    return bool(
        payload.documentLooksLikeSchedule
        and payload.university.strip()
        and payload.semester.strip()
        and payload.courses
    )


def _classification_confidence(payload: ScheduleDocumentPayload) -> float:
    score = 0
    if payload.documentLooksLikeSchedule:
        score += 0.35
    if payload.university.strip():
        score += 0.2
    if payload.semester.strip():
        score += 0.2
    if payload.courses:
        score += 0.25
    return round(score, 2)


def _extract_document_text(file_path: Path, mime_type: str) -> str:
    if mime_type == "application/pdf":
        text = _extract_pdf_text(file_path)
        if len(_normalize_whitespace(text)) >= 80:
            return text
        ocr_text = _ocr_pdf(file_path)
        return ocr_text if len(_normalize_whitespace(ocr_text)) > len(_normalize_whitespace(text)) else text

    text = _ocr_image(file_path)
    return text


def _extract_pdf_text(file_path: Path) -> str:
    try:
        import fitz
    except ImportError as exc:
        raise ValueError("PyMuPDF is required for local PDF schedule extraction") from exc

    parts: list[str] = []
    with fitz.open(file_path) as document:
        for page in document:
            text = page.get_text("text") or ""
            if text.strip():
                parts.append(text)
    return "\n".join(parts).strip()


def _ocr_pdf(file_path: Path) -> str:
    try:
        import fitz
    except ImportError as exc:
        raise ValueError("PyMuPDF is required for OCRing PDF schedules") from exc

    texts: list[str] = []
    with fitz.open(file_path) as document:
        for page in document:
            pixmap = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
            texts.append(_ocr_bytes(pixmap.tobytes("png")))
    return "\n".join(part for part in texts if part.strip()).strip()


def _ocr_image(file_path: Path) -> str:
    return _ocr_bytes(file_path.read_bytes())


def _ocr_bytes(image_bytes: bytes) -> str:
    try:
        import pytesseract
        from PIL import Image
    except ImportError as exc:
        raise ValueError("pytesseract and Pillow are required for OCR schedule extraction") from exc

    from io import BytesIO

    try:
        image = Image.open(BytesIO(image_bytes))
    except Exception as exc:
        raise ValueError(f"unable to read image for OCR: {exc}") from exc

    try:
        return pytesseract.image_to_string(image, lang="eng+ara").strip()
    except pytesseract.TesseractNotFoundError as exc:
        raise ValueError("Tesseract OCR is not installed or not in PATH") from exc


def _extract_schedule_fields(text: str) -> dict[str, Any]:
    normalized_text = _normalize_whitespace(text)
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    lower_text = normalized_text.lower()

    keyword_hits = sum(1 for keyword in SCHEDULE_KEYWORDS if keyword.lower() in lower_text)
    semester = _extract_semester(normalized_text)
    courses = _extract_courses(lines)
    university = _extract_university(lines)
    student_name = _extract_student_name(lines)
    document_looks_like_schedule = keyword_hits >= 2 and bool(semester or courses)

    return {
        "documentLooksLikeSchedule": document_looks_like_schedule,
        "studentName": student_name,
        "university": university,
        "semester": semester,
        "isCurrentSemester": bool(semester),
        "courses": courses,
    }


def _extract_semester(text: str) -> str:
    match = SEMESTER_PATTERN.search(text)
    if match:
        return match.group(0).strip()

    arabic_match = ARABIC_SEMESTER_PATTERN.search(text)
    if arabic_match:
        return arabic_match.group(0).strip()

    return ""


def _extract_courses(lines: list[str]) -> list[str]:
    courses: list[str] = []
    seen: set[str] = set()
    for line in lines:
        cleaned = _normalize_whitespace(line)
        if not cleaned:
            continue
        if COURSE_LINE_PATTERN.search(cleaned):
            normalized = cleaned.lower()
            if normalized not in seen:
                seen.add(normalized)
                courses.append(cleaned)
    return courses[:15]


def _extract_university(lines: list[str]) -> str:
    for line in lines:
        cleaned = _normalize_whitespace(line)
        lowered = cleaned.lower()
        if "university" in lowered or "جامعة" in cleaned:
            return cleaned
    return ""


def _extract_student_name(lines: list[str]) -> str:
    for line in lines:
        cleaned = _normalize_whitespace(line)
        lowered = cleaned.lower()
        if lowered.startswith("name"):
            return cleaned.split(":", 1)[-1].strip() if ":" in cleaned else cleaned
        if "student name" in lowered or "اسم الطالب" in cleaned:
            return cleaned.split(":", 1)[-1].strip() if ":" in cleaned else cleaned
    return ""


def _normalize_whitespace(value: str) -> str:
    return " ".join((value or "").split())


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
    mime_type = (payload.mimeType or "").strip().lower()
    if mime_type:
        return mime_type

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
