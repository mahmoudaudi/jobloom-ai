from __future__ import annotations

import mimetypes
import re
from io import BytesIO
from pathlib import Path

from transcript_verification.application.dtos import TranscriptDocumentPayload


SUPPORTED_MIME_TYPES = {
    "application/pdf",
    "image/png",
    "image/jpeg",
    "image/webp",
}
URL_PATTERN = re.compile(r"https?://\S+", re.IGNORECASE)
EMAIL_PATTERN = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
GPA_PATTERN = re.compile(r"\bGPA\b[:\s]*([0-4](?:\.\d{1,2})?)", re.IGNORECASE)
COURSE_PATTERN = re.compile(r"\b[A-Z]{2,}\s*[-/]?\s*\d{2,3}[A-Z]?\b")
SEMESTER_PATTERN = re.compile(r"\b(Spring|Summer|Fall|Winter|Autumn)\s+20\d{2}\b|\b20\d{2}\s+(Spring|Summer|Fall|Winter|Autumn)\b", re.IGNORECASE)
TRANSCRIPT_KEYWORDS = (
    "transcript",
    "transcript of records",
    "grade point average",
    "gpa",
    "registrar",
    "credits",
    "courses",
    "الدرجات",
    "السجل الأكاديمي",
    "كشف العلامات",
    "certifies that",
    "attending classes regularly",
    "student affairs",
    "attestation",
    "certificate",
)
DEGREE_HINTS = ("bachelor", "master", "b.sc", "bsc", "bs ", "mba", "phd")
MAJOR_HINTS = (
    "computer science",
    "software engineering",
    "information technology",
    "computer engineering",
    "marketing",
    "finance",
    "design",
    "business administration",
)


class LocalTranscriptExtractor:
    def extract(self, payload: TranscriptDocumentPayload) -> TranscriptDocumentPayload:
        file_path = _resolve_file_path(payload)
        mime_type = _detect_mime_type(payload, file_path)
        if mime_type not in SUPPORTED_MIME_TYPES:
            raise ValueError("transcript file must be PDF, PNG, JPEG, or WEBP")

        text = _extract_document_text(file_path, mime_type)
        fields = _extract_transcript_fields(text)

        return TranscriptDocumentPayload(
            filePath=str(file_path),
            fileUrl=payload.fileUrl,
            fileName=payload.fileName or file_path.name,
            mimeType=mime_type,
            documentLooksLikeTranscript=fields["documentLooksLikeTranscript"],
            studentName=fields["studentName"],
            university=fields["university"],
            degree=fields["degree"],
            major=fields["major"],
            gpa=fields["gpa"],
            lastSemester=fields["lastSemester"],
            courses=fields["courses"],
            hasVerificationUrl=fields["hasVerificationUrl"],
            hasDigitalSignature=_has_pdf_signature(file_path) if mime_type == "application/pdf" else False,
        )


def _extract_document_text(file_path: Path, mime_type: str) -> str:
    if mime_type == "application/pdf":
        text = _extract_pdf_text(file_path)
        if len(_normalize_whitespace(text)) >= 100:
            return text
        ocr_text = _ocr_pdf(file_path)
        return ocr_text if len(_normalize_whitespace(ocr_text)) > len(_normalize_whitespace(text)) else text
    return _ocr_image(file_path)


def _extract_pdf_text(file_path: Path) -> str:
    import fitz

    parts: list[str] = []
    with fitz.open(file_path) as document:
        for page in document:
            page_text = page.get_text("text") or ""
            if page_text.strip():
                parts.append(page_text)
    return "\n".join(parts).strip()


def _ocr_pdf(file_path: Path) -> str:
    import fitz

    texts: list[str] = []
    with fitz.open(file_path) as document:
        for page in document:
            pixmap = page.get_pixmap(matrix=fitz.Matrix(4, 4), alpha=False)
            texts.append(_ocr_bytes(pixmap.tobytes("png")))
    return "\n".join(part for part in texts if part.strip()).strip()


def _ocr_image(file_path: Path) -> str:
    return _ocr_bytes(file_path.read_bytes())


def _ocr_bytes(image_bytes: bytes) -> str:
    import pytesseract
    from PIL import Image
    from PIL import ImageFilter, ImageOps

    default_path = Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe")
    if default_path.exists():
        pytesseract.pytesseract.tesseract_cmd = str(default_path)
    image = Image.open(BytesIO(image_bytes))
    image = ImageOps.grayscale(image)
    image = ImageOps.autocontrast(image)
    image = image.filter(ImageFilter.SHARPEN)
    return pytesseract.image_to_string(
        image,
        lang="eng+ara",
        config="--oem 3 --psm 6",
    ).strip()


def _extract_transcript_fields(text: str) -> dict:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    normalized_text = _normalize_whitespace(text)
    lower_text = normalized_text.lower()

    keyword_hits = sum(1 for keyword in TRANSCRIPT_KEYWORDS if keyword in lower_text)
    document_looks_like_transcript = keyword_hits >= 2 and (
        "gpa" in lower_text
        or "course" in lower_text
        or "credit" in lower_text
        or "certifies that" in lower_text
        or "attending classes regularly" in lower_text
    )

    student_name = _extract_student_name(lines)
    university = _extract_university(lines)
    degree = next((line for line in lines[:25] if any(hint in line.lower() for hint in DEGREE_HINTS)), "")
    major = next((hint.title() for hint in MAJOR_HINTS if hint in lower_text), "")
    gpa = _extract_gpa(lines)
    last_semester = _extract_last_semester(normalized_text)
    courses = _extract_courses(lines)
    has_verification_url = any(_looks_like_verification_url(url) for url in URL_PATTERN.findall(text))

    return {
        "documentLooksLikeTranscript": document_looks_like_transcript,
        "studentName": student_name,
        "university": university,
        "degree": degree,
        "major": major,
        "gpa": gpa,
        "lastSemester": last_semester,
        "courses": courses,
        "hasVerificationUrl": has_verification_url,
    }


def _extract_student_name(lines: list[str]) -> str:
    for line in lines:
        lowered = line.lower()
        if lowered.startswith("name"):
            return line.split(":", 1)[-1].strip() if ":" in line else line
        if "student name" in lowered or "name of student" in lowered:
            return line.split(":", 1)[-1].strip() if ":" in line else line
        if "certifies that" in lowered:
            tail = line.split("certifies that", 1)[-1].strip(" :")
            tail = re.sub(r"[^A-Za-z\s]", " ", tail)
            tail = " ".join(tail.split())
            return tail
    candidates = [line for line in lines[:10] if 2 <= len(line.split()) <= 4 and not EMAIL_PATTERN.search(line)]
    return candidates[0] if candidates else ""


def _extract_university(lines: list[str]) -> str:
    for line in lines:
        lowered = line.lower()
        if "beirut arab university" in lowered:
            return "Beirut Arab University"
        if "university" in lowered or "college" in lowered or "جامعة" in line:
            return line
    return ""


def _extract_gpa(lines: list[str]) -> float | None:
    for line in lines:
        match = GPA_PATTERN.search(line)
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                return None
    return None


def _extract_last_semester(text: str) -> str:
    match = SEMESTER_PATTERN.search(text)
    return match.group(0).strip() if match else ""


def _extract_courses(lines: list[str]) -> list[str]:
    courses: list[str] = []
    seen: set[str] = set()
    for line in lines:
        cleaned = _normalize_whitespace(line)
        if COURSE_PATTERN.search(cleaned):
            normalized = cleaned.lower()
            if normalized not in seen:
                seen.add(normalized)
                courses.append(cleaned)
    return courses[:20]


def _looks_like_verification_url(url: str) -> bool:
    lowered = url.lower()
    return any(token in lowered for token in ("verify", "verification", "transcript", "student", "record"))


def _has_pdf_signature(file_path: Path) -> bool:
    try:
        from pypdf import PdfReader
    except ImportError:
        return False

    try:
        reader = PdfReader(str(file_path))
    except Exception:
        return False

    try:
        root = reader.trailer["/Root"]
        acro_form = root.get("/AcroForm")
        if not acro_form:
            return False
        fields = acro_form.get("/Fields", [])
        for field in fields:
            field_obj = field.get_object()
            if field_obj.get("/FT") == "/Sig":
                return True
    except Exception:
        return False
    return False


def _normalize_whitespace(value: str) -> str:
    return " ".join((value or "").split())


def _resolve_file_path(payload: TranscriptDocumentPayload) -> Path:
    source = payload.filePath or payload.fileUrl
    if not source:
        raise ValueError("transcript filePath or fileUrl is required for extraction")
    path = Path(source)
    if not path.is_absolute():
        path = Path.cwd() / source.lstrip("/\\")
    if not path.exists() or not path.is_file():
        raise ValueError(f"transcript file not found: {path}")
    return path


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
