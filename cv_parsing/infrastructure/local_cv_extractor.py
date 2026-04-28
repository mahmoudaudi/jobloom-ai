from __future__ import annotations

import re
from io import BytesIO
from pathlib import Path

import fitz
import pytesseract
from PIL import Image

from cv_parsing.application.dtos import ParseCvRequest
from cv_parsing.domain.models import (
    ConfidenceInfo,
    EducationInfo,
    ExperienceInfo,
    ParsedCv,
    PersonalInfo,
)


EMAIL_PATTERN = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
PHONE_PATTERN = re.compile(r"(\+?\d[\d\s().-]{7,}\d)")
GPA_PATTERN = re.compile(r"\bGPA\b[:\s]*([0-4](?:\.\d{1,2})?)", re.IGNORECASE)
YEAR_PATTERN = re.compile(r"\b(20\d{2})\s*[-/]\s*(20\d{2})\b")
GRAD_PATTERN = re.compile(r"(?:expected graduation|graduation|expected to graduate)[:\s-]*(20\d{2})", re.IGNORECASE)
EXPECTED_INLINE_PATTERN = re.compile(r",?\s*expected\s+(20\d{2})", re.IGNORECASE)
YEAR_LABEL_PATTERN = re.compile(r"\bYear\s+\d+\s+of\s+\d+\b", re.IGNORECASE)
UNDERGRAD_YEAR_PATTERN = re.compile(r"\b(first|second|third|fourth|fifth)[-\s]?year\b", re.IGNORECASE)
SKILLS_HEADER_PATTERN = re.compile(r"^(skills|technical skills|technologies)\b", re.IGNORECASE)
EXPERIENCE_HEADER_PATTERN = re.compile(r"^(experience|work experience|employment|professional experience)\b", re.IGNORECASE)
EDUCATION_HEADER_PATTERN = re.compile(r"^education\b", re.IGNORECASE)
SECTION_STOP_PATTERN = re.compile(r"^(projects|certifications|languages|activities|summary|profile)\b", re.IGNORECASE)
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
DEGREE_HINTS = ("bachelor", "master", "b.sc", "bsc", "bs ", "mba", "phd")
SKILL_KEYWORDS = (
    "react",
    "typescript",
    "javascript",
    "node.js",
    "git",
    "sql",
    "mysql",
    "java",
    "kotlin",
    "python",
    "figma",
    "html",
    "css",
    "express",
    "fastapi",
    "php",
    "microsoft word",
    "excel",
    "powerpoint",
)
CITY_COUNTRY_PATTERN = re.compile(r"([A-Za-z]+(?:\s+[A-Za-z]+)*),\s*([A-Za-z]+(?:\s+[A-Za-z]+)*)")
EXPERIENCE_TITLE_PATTERN = re.compile(r".+,\s*.+")
HEADER_WORDS = {"skills", "award", "education", "certification", "work experience", "technical skills", "teaching & office skills"}
EXPERIENCE_STOP_HEADERS = {"technical skills", "teaching & office skills"}
LOCATION_BLACKLIST = {"expected", "bachelor", "science", "databases", "development", "engineering", "skills", "experience", "coursework"}
SKILL_BLACKLIST = {"award", "fala", "march", "august", "present", "spreadsheets", "presentations"}


class LocalCvExtractor:
    def extract(self, payload: ParseCvRequest) -> ParsedCv:
        text = self.extract_text(payload)
        return self.parse_text(text)

    def extract_text(self, payload: ParseCvRequest) -> str:
        file_path = _resolve_file_path(payload.filePath or payload.fileUrl or "")
        return _extract_document_text(file_path)

    def parse_text(self, text: str) -> ParsedCv:
        lines = [line.strip() for line in text.splitlines() if line.strip()]

        personal = _extract_personal(lines)
        education = _extract_education(lines)
        skills = _extract_skills(lines, text)
        experiences = _extract_experiences(lines)
        confidence = _build_confidence(personal, education, skills, experiences)

        return ParsedCv(
            personal=personal,
            education=education,
            skills=skills,
            experiences=experiences,
            confidence=confidence,
            rawText=text[:4000],
            language="ar" if re.search(r"[\u0600-\u06FF]", text) else "en",
        )


def _resolve_file_path(source: str) -> Path:
    path = Path(source)
    if not path.is_absolute():
        path = Path.cwd() / source.lstrip("/\\")
    if not path.exists() or not path.is_file():
        raise ValueError(f"cv file not found: {path}")
    return path


def _extract_document_text(file_path: Path) -> str:
    if file_path.suffix.lower() == ".pdf":
        text = _extract_pdf_text(file_path)
        if len(_normalize_whitespace(text)) >= 120:
            return text
        ocr_text = _ocr_pdf(file_path)
        return ocr_text if len(_normalize_whitespace(ocr_text)) > len(_normalize_whitespace(text)) else text
    return _ocr_image(file_path)


def _extract_pdf_text(file_path: Path) -> str:
    parts: list[str] = []
    with fitz.open(file_path) as document:
        for page in document:
            page_text = page.get_text("text") or ""
            if page_text.strip():
                parts.append(page_text)
    return "\n".join(parts).strip()


def _ocr_pdf(file_path: Path) -> str:
    texts: list[str] = []
    with fitz.open(file_path) as document:
        for page in document:
            pixmap = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
            texts.append(_ocr_bytes(pixmap.tobytes("png")))
    return "\n".join(part for part in texts if part.strip()).strip()


def _ocr_image(file_path: Path) -> str:
    return _ocr_bytes(file_path.read_bytes())


def _ocr_bytes(image_bytes: bytes) -> str:
    default_path = Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe")
    if default_path.exists():
        pytesseract.pytesseract.tesseract_cmd = str(default_path)
    image = Image.open(BytesIO(image_bytes))
    return pytesseract.image_to_string(image, lang="eng+ara").strip()


def _extract_personal(lines: list[str]) -> PersonalInfo:
    full_name = ""
    email = ""
    phone = ""
    country = ""
    city = ""

    for line in lines[:20]:
        if not full_name and _looks_like_name(line):
            full_name = line
        if not email and (match := EMAIL_PATTERN.search(line)):
            email = match.group(0)
        if not phone and (match := PHONE_PATTERN.search(line)):
            phone = re.sub(r"[^\d+]", "", match.group(1))
        if not city and not country and _looks_like_location_line(line):
            match = CITY_COUNTRY_PATTERN.search(line)
            if match:
                city, country = match.group(1).strip(), match.group(2).strip()

    return PersonalInfo(fullName=full_name, email=email, phone=phone, country=country, city=city)


def _extract_education(lines: list[str]) -> EducationInfo:
    block = _extract_section(lines, EDUCATION_HEADER_PATTERN)
    search_lines = block or lines[:35]
    fallback_lines = lines[:35]

    degree = next((line for line in search_lines if any(hint in line.lower() for hint in DEGREE_HINTS)), "")
    university = next((line for line in search_lines if "university" in line.lower() or "جامعة" in line), "")
    major = _extract_major(search_lines, degree)
    year_label = next((match.group(0) for line in search_lines if (match := YEAR_LABEL_PATTERN.search(line))), "")
    if not year_label:
        year_label = _infer_year_label(search_lines)

    education_period = ""
    expected_graduation = ""
    gpa = None
    for line in search_lines:
        if not education_period and (match := YEAR_PATTERN.search(line)):
            education_period = f"{match.group(1)} - {match.group(2)}"
            expected_graduation = match.group(2)
        if not expected_graduation and (match := GRAD_PATTERN.search(line)):
            expected_graduation = match.group(1)
        if not expected_graduation and (match := EXPECTED_INLINE_PATTERN.search(line)):
            expected_graduation = match.group(1)
        if gpa is None and (match := GPA_PATTERN.search(line)):
            try:
                gpa = float(match.group(1))
            except ValueError:
                gpa = None

    if not degree:
        degree = next((line for line in fallback_lines if any(hint in line.lower() for hint in DEGREE_HINTS)), "")
    if not university:
        university = next((line for line in fallback_lines if "university" in line.lower() or "جامعة" in line), "")
    if not major:
        major = _extract_major(fallback_lines, degree)
    if not year_label:
        year_label = next((match.group(0) for line in fallback_lines if (match := YEAR_LABEL_PATTERN.search(line))), "")
        if not year_label:
            year_label = _infer_year_label(fallback_lines)
    if not education_period or not expected_graduation:
        for line in fallback_lines:
            if not education_period and (match := YEAR_PATTERN.search(line)):
                education_period = f"{match.group(1)} - {match.group(2)}"
                expected_graduation = expected_graduation or match.group(2)
            if not expected_graduation and (match := GRAD_PATTERN.search(line)):
                expected_graduation = match.group(1)
            if not expected_graduation and (match := EXPECTED_INLINE_PATTERN.search(line)):
                expected_graduation = match.group(1)
            if not education_period and _looks_like_education_period_line(line):
                education_period = line.strip()

    degree = _clean_degree(degree)

    return EducationInfo(
        degree=degree,
        majorName=major,
        university=university,
        yearLabel=year_label,
        educationPeriod=education_period,
        expectedGraduation=expected_graduation,
        gpa=gpa,
    )


def _extract_skills(lines: list[str], text: str) -> list[str]:
    block = _extract_skills_block(lines)
    candidates: list[str] = []
    for line in block:
        value = line.split(":", 1)[1] if ":" in line else line
        candidates.extend(re.split(r"[,|/•()]", value))
    for keyword in SKILL_KEYWORDS:
        if keyword in text.lower():
            candidates.append(keyword)

    skills: list[str] = []
    seen: set[str] = set()
    for item in candidates:
        cleaned = _clean_skill(item)
        if cleaned and cleaned.lower() not in seen:
            seen.add(cleaned.lower())
            skills.append(cleaned)
    return skills[:20]


def _extract_experiences(lines: list[str]) -> list[ExperienceInfo]:
    start_index = -1
    for index, line in enumerate(lines):
        if EXPERIENCE_HEADER_PATTERN.search(line):
            start_index = index + 1
            break

    if start_index == -1:
        return []

    block = lines[start_index:]
    experiences: list[ExperienceInfo] = []
    index = 0
    while index < len(block) and len(experiences) < 5:
        title = block[index]
        lowered_title = title.lower().strip()
        if lowered_title in EXPERIENCE_STOP_HEADERS:
            index += 1
            while index < len(block):
                candidate = block[index]
                next_candidate = block[index + 1] if index + 1 < len(block) else ""
                previous_candidate = block[index - 1] if index > 0 else ""
                if _looks_like_experience_title(candidate, next_line=next_candidate) or (
                    _looks_like_period_line(candidate)
                    and _looks_like_experience_title(next_candidate, next_line=block[index + 2] if index + 2 < len(block) else "")
                ) or (
                    _looks_like_experience_title(candidate, next_line="")
                    and _looks_like_period_line(previous_candidate)
                ):
                    break
                index += 1
            continue

        next_line = block[index + 1] if index + 1 < len(block) else ""
        previous_line = block[index - 1] if index > 0 else ""
        if not _looks_like_experience_title(title, next_line=next_line):
            if _looks_like_period_line(title) and _looks_like_experience_title(next_line, next_line=block[index + 2] if index + 2 < len(block) else ""):
                previous_line = title
                title = next_line
                next_line = block[index + 2] if index + 2 < len(block) else ""
                index += 1
            elif _looks_like_experience_title(title, next_line="") and _looks_like_period_line(next_line):
                pass
            else:
                index += 1
                continue

        company = ""
        period = ""
        description_parts: list[str] = []
        cursor = index + 1
        while cursor < len(block):
            current = block[cursor]
            next_current = block[cursor + 1] if cursor + 1 < len(block) else ""
            if current.lower().strip() in EXPERIENCE_STOP_HEADERS:
                break
            if cursor != index + 1 and _looks_like_experience_title(current, next_line=next_current):
                break
            if cursor != index + 1 and _looks_like_period_line(current) and _looks_like_experience_title(next_current, next_line=block[cursor + 2] if cursor + 2 < len(block) else ""):
                break
            if not period and _looks_like_period_line(current):
                period = current
            elif current and current != company and current.lower() not in HEADER_WORDS:
                description_parts.append(current)
            cursor += 1

        title_text, company_text = _split_title_company(title)
        if company_text:
            company = company_text
        if not period and _looks_like_period_line(previous_line):
            period = previous_line
        experiences.append(
            ExperienceInfo(
                title=title_text,
                company=company,
                period=period,
                description=" ".join(description_parts[:4]).strip(),
            )
        )
        index = cursor

    return [item for item in experiences if item.title]


def _extract_section(lines: list[str], header_pattern: re.Pattern[str]) -> list[str]:
    start_index = -1
    for index, line in enumerate(lines):
        if header_pattern.search(line):
            start_index = index + 1
            break
    if start_index == -1:
        return []

    section: list[str] = []
    for line in lines[start_index:]:
        if SECTION_STOP_PATTERN.search(line):
            break
        if (
            header_pattern != EXPERIENCE_HEADER_PATTERN and EXPERIENCE_HEADER_PATTERN.search(line)
        ) or (
            header_pattern != SKILLS_HEADER_PATTERN and SKILLS_HEADER_PATTERN.search(line)
        ) or (
            header_pattern != EDUCATION_HEADER_PATTERN and EDUCATION_HEADER_PATTERN.search(line)
        ):
            break
        section.append(line)
    return section


def _extract_skills_block(lines: list[str]) -> list[str]:
    preferred_headers = ("technical skills", "skills", "teaching & office skills")
    for header in preferred_headers:
        start = -1
        for index, line in enumerate(lines):
            if line.lower().startswith(header):
                start = index
                break
        if start == -1:
            continue

        collected: list[str] = []
        for line in lines[start : start + 8]:
            if line != lines[start] and _looks_like_experience_title(line):
                break
            if line.lower() in HEADER_WORDS:
                continue
            collected.append(line)
        if collected:
            return collected
    return _extract_section(lines, SKILLS_HEADER_PATTERN)


def _build_confidence(
    personal: PersonalInfo,
    education: EducationInfo,
    skills: list[str],
    experiences: list[ExperienceInfo],
) -> ConfidenceInfo:
    personal_score = round(sum(1 for value in (personal.fullName, personal.email, personal.phone, personal.city or personal.country) if value) / 4, 2)
    education_score = round(sum(1 for value in (education.degree, education.majorName, education.university, education.yearLabel or education.educationPeriod or education.expectedGraduation) if value) / 4, 2)
    skills_score = round(min(len(skills), 6) / 6, 2)
    experiences_score = round(min(len(experiences), 3) / 3, 2)
    overall = round((personal_score + education_score + skills_score + experiences_score) / 4, 2)
    return ConfidenceInfo(
        overall=overall,
        personal=personal_score,
        education=education_score,
        skills=skills_score,
        experiences=experiences_score,
    )


def _extract_major(search_lines: list[str], degree: str) -> str:
    for line in search_lines:
        lowered = line.lower()
        for hint in MAJOR_HINTS:
            if hint in lowered:
                return hint.title()
    if " in " in degree.lower():
        return degree.split(" in ", 1)[1].split(",")[0].strip()
    return ""


def _infer_year_label(search_lines: list[str]) -> str:
    mapping = {
        "first": "Year 1 of 4",
        "second": "Year 2 of 4",
        "third": "Year 3 of 4",
        "fourth": "Year 4 of 4",
        "fifth": "Year 5 of 5",
    }
    for line in search_lines:
        if match := UNDERGRAD_YEAR_PATTERN.search(line):
            return mapping.get(match.group(1).lower(), "")
    return ""


def _looks_like_name(line: str) -> bool:
    if any(token in line.lower() for token in ("email", "phone", "linkedin", "github", "university")):
        return False
    words = [word for word in re.split(r"\s+", line.strip()) if word]
    return 2 <= len(words) <= 4 and all(word and word[0].isalpha() for word in words)


def _looks_like_heading(line: str) -> bool:
    stripped = line.strip()
    return 3 <= len(stripped) <= 80 and not EMAIL_PATTERN.search(stripped) and any(char.isalpha() for char in stripped)


def _looks_like_experience_title(line: str, next_line: str = "") -> bool:
    stripped = line.strip()
    lowered = stripped.lower()
    if not stripped or lowered in HEADER_WORDS:
        return False
    if EMAIL_PATTERN.search(stripped):
        return False
    if ":" in stripped:
        return False
    if not EXPERIENCE_TITLE_PATTERN.fullmatch(stripped):
        return False
    if stripped.count(",") != 1:
        return False
    title_part, company_part = [part.strip() for part in stripped.split(",", 1)]
    if not title_part or not company_part:
        return False
    if len(title_part.split()) > 5 or len(company_part.split()) > 5:
        return False
    if any(ch in stripped for ch in "()"):
        return False
    if _looks_like_period_line(next_line) or "present" in next_line.lower():
        return True
    return True


def _looks_like_period_line(line: str) -> bool:
    return bool(
        re.search(
            r"\b(20\d{2}|present|current|jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)\b",
            line.lower(),
        )
    )


def _clean_skill(value: str) -> str:
    cleaned = _normalize_whitespace(value)
    cleaned = re.sub(r"^(skills|technical skills)[:\s-]*", "", cleaned, flags=re.IGNORECASE)
    lowered = cleaned.lower()
    if (
        not cleaned
        or len(cleaned) > 30
        or lowered in HEADER_WORDS
        or lowered in SKILL_BLACKLIST
        or re.search(r"\d{2,4}", cleaned)
        or "," in cleaned
    ):
        return ""
    if lowered not in SKILL_KEYWORDS and (
        len(cleaned.split()) > 2
        or any(word in lowered for word in ("and", "with", "ability", "used", "data", "entry"))
    ):
        return ""
    return (
        cleaned.title()
        .replace("Sql", "SQL")
        .replace("Javascript", "JavaScript")
        .replace("Typescript", "TypeScript")
        .replace("Mysql", "MySQL")
        .replace("Html", "HTML")
        .replace("Css", "CSS")
        .replace("Php", "PHP")
        .replace("Powerpoint", "PowerPoint")
    )


def _clean_degree(value: str) -> str:
    cleaned = _normalize_whitespace(value)
    cleaned = EXPECTED_INLINE_PATTERN.sub("", cleaned).strip(" ,")
    return cleaned


def _split_title_company(value: str) -> tuple[str, str]:
    if "," not in value:
        return value.strip(), ""
    title, company = value.split(",", 1)
    return title.strip(), company.strip()


def _looks_like_location_line(line: str) -> bool:
    lowered = line.lower().strip()
    if any(term in lowered for term in ("university", "certified", "skills", "experience", "coursework", ":")):
        return False
    match = CITY_COUNTRY_PATTERN.search(line)
    if not match:
        return False
    left = match.group(1).strip().split()
    right = match.group(2).strip().split()
    if not (1 <= len(left) <= 3 and 1 <= len(right) <= 3):
        return False
    if any(word.lower() in LOCATION_BLACKLIST for word in left + right):
        return False
    return all(word[:1].isupper() for word in left + right if word)


def _looks_like_education_period_line(line: str) -> bool:
    lowered = line.lower()
    if "present" not in lowered:
        return False
    return bool(re.search(r"20\d{2}|jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec", lowered))


def _normalize_whitespace(value: str) -> str:
    return " ".join((value or "").split())
