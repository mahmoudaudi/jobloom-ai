from __future__ import annotations

import re
from typing import List, Sequence, Tuple

from .models import Experience, Job, StudentProfile


WORD_RE = re.compile(r"[A-Za-z0-9+#.]+")

SKILL_SYNONYMS = {
    "js": "javascript",
    "javascript": "javascript",
    "ts": "typescript",
    "typescript": "typescript",
    "reactjs": "react",
    "react.js": "react",
    "react": "react",
    "reactnative": "react native",
    "react-native": "react native",
    "node": "node.js",
    "nodejs": "node.js",
    "node.js": "node.js",
    "expressjs": "express",
    "express.js": "express",
    "sql": "sql",
    "mysql": "sql",
    "postgresql": "sql",
    "postgres": "sql",
    "mssql": "sql",
    "html5": "html",
    "css3": "css",
    "uiux": "ui ux",
    "ui/ux": "ui ux",
    "problem solving": "problem solving",
    "communication skills": "communication",
}

CATEGORY_ALIASES = {
    "it": {
        "it",
        "computer science",
        "software",
        "software engineering",
        "information technology",
        "information systems",
        "computer engineering",
        "data science",
        "cybersecurity",
        "cyber security",
        "developer",
        "backend",
        "frontend",
        "engineering",
    },
    "marketing": {"marketing", "media", "content", "advertising", "communications"},
    "finance": {"finance", "accounting", "economics", "banking", "investment"},
    "design": {"design", "ui", "ux", "graphic", "product design", "creative"},
}


def _normalize(text: str) -> str:
    return text.strip().lower()


def _tokenize(text: str) -> List[str]:
    return [token.lower() for token in WORD_RE.findall(text)]


def _normalize_skill(text: str) -> str:
    cleaned = text.strip()
    cleaned = re.sub(r"\s*\d+(\.\d+)*\b", "", cleaned)
    cleaned = cleaned.strip(" ,;:/")
    key = re.sub(r"[^a-z0-9+#.]+", " ", cleaned.lower()).strip()
    if not key:
        return ""
    return SKILL_SYNONYMS.get(key, key)


def _normalize_requirements(requirements: Sequence[str] | str) -> List[str]:
    if isinstance(requirements, str):
        raw_items = re.split(r"[,;/|]", requirements)
    else:
        raw_items = list(requirements)

    result: List[str] = []
    seen = set()
    for raw in raw_items:
        item = _normalize_skill(str(raw))
        if not item:
            continue
        key = _normalize(item)
        if key in seen:
            continue
        seen.add(key)
        result.append(item)
    return result


def _tokens_match(left: str, right: str) -> bool:
    left_tokens = set(_tokenize(left))
    right_tokens = set(_tokenize(right))
    if not left_tokens or not right_tokens:
        return False
    return left_tokens.issubset(right_tokens) or right_tokens.issubset(left_tokens)


def _skill_overlap(student_skills: Sequence[str], job_requirements: Sequence[str]) -> float:
    if not job_requirements:
        return 0.0
    normalized_student_skills = [
        _normalize_skill(skill) for skill in student_skills if str(skill).strip()
    ]
    normalized_student_skills = [skill for skill in normalized_student_skills if skill]
    normalized_requirements = [
        _normalize_skill(req) for req in job_requirements if str(req).strip()
    ]
    normalized_requirements = [req for req in normalized_requirements if req]
    if not normalized_requirements:
        return 0.0

    matched = 0
    for requirement in normalized_requirements:
        if any(
            skill == requirement
            or skill in requirement
            or requirement in skill
            or _tokens_match(skill, requirement)
            for skill in normalized_student_skills
        ):
            matched += 1

    return matched / max(1, len(normalized_requirements))


def _major_matches_category(major: str, category: str) -> bool:
    major_value = _normalize(major)
    category_value = _normalize(category)
    if not major_value or not category_value:
        return False
    if major_value == category_value:
        return True
    aliases = CATEGORY_ALIASES.get(category_value, set())
    if major_value in aliases:
        return True
    return any(alias in major_value or major_value in alias for alias in aliases)


def _location_score(student: StudentProfile, job: Job) -> float:
    if _normalize(job.type) == "remote":
        return 0.35

    student_city = _normalize(student.location.city)
    student_country = _normalize(student.location.country)

    parts = [part.strip() for part in job.locationText.split(",") if part.strip()]
    if not parts:
        return 0.0

    job_city = _normalize(parts[0])
    job_country = _normalize(parts[-1]) if len(parts) > 1 else ""

    if student_city and student_city == job_city:
        return 1.0
    if student_country and student_country == job_country:
        return 0.55
    return 0.0


def _keyword_overlap(text_a: str, text_b: str) -> float:
    tokens_a = set(_tokenize(text_a))
    tokens_b = set(_tokenize(text_b))
    if not tokens_a or not tokens_b:
        return 0.0
    return len(tokens_a.intersection(tokens_b)) / max(1, len(tokens_b))


def _experience_relevance(experiences: Sequence[Experience], job: Job) -> float:
    if not experiences:
        return 0.0
    job_context = f"{job.title} {job.description} {' '.join(job.requirements)} {job.category}"
    relevance = max(
        _keyword_overlap(
            f"{experience.title} {experience.company} {experience.description}",
            job_context,
        )
        for experience in experiences
    )
    return relevance if relevance >= 0.12 else 0.0


def score_job_match(student: StudentProfile, job: Job) -> Tuple[int, List[str]]:
    requirements = _normalize_requirements(job.requirements)
    skill_overlap = _skill_overlap(student.skills, requirements)
    major_match = 1.0 if _major_matches_category(student.major, job.category) else 0.0
    location_score = _location_score(student, job)
    experience_relevance = _experience_relevance(student.experiences, job)

    score = (
        0.50 * skill_overlap
        + 0.20 * major_match
        + 0.15 * location_score
        + 0.15 * experience_relevance
    )
    match_percentage = max(0, min(100, round(score * 100)))

    reasons: List[str] = []
    if requirements:
        matched = round(skill_overlap * len(requirements))
        reasons.append(f"{matched}/{len(requirements)} skills match")
    if major_match:
        reasons.append("Major aligned")
    if location_score == 1.0:
        reasons.append("Same city")
    elif location_score == 0.5:
        reasons.append("Same country")
    elif location_score == 0.3:
        reasons.append("Remote-friendly")
    if experience_relevance > 0:
        reasons.append("Relevant experience found")

    if not reasons:
        reasons.append("Limited direct overlap")

    return match_percentage, reasons[:4]


def match_label(match_percentage: int) -> str:
    if match_percentage >= 85:
        return "Excellent match"
    if match_percentage >= 70:
        return "Great match"
    if match_percentage >= 50:
        return "Good match"
    return "Potential match"
