from __future__ import annotations

from typing import Any

from cv_parsing.domain.models import ParsedCv


def build_parse_cv_response(result: ParsedCv) -> dict[str, Any]:
    return {
        "success": True,
        "data": {
            "personal": {
                "fullName": result.personal.fullName,
                "email": result.personal.email,
                "phone": result.personal.phone,
                "country": result.personal.country,
                "city": result.personal.city,
            },
            "education": {
                "degree": result.education.degree,
                "majorName": result.education.majorName,
                "university": result.education.university,
                "yearLabel": result.education.yearLabel,
                "educationPeriod": result.education.educationPeriod,
                "expectedGraduation": result.education.expectedGraduation,
                "gpa": result.education.gpa,
            },
            "skills": result.skills,
            "experiences": [
                {
                    "title": item.title,
                    "company": item.company,
                    "period": item.period,
                    "description": item.description,
                }
                for item in result.experiences
            ],
            "confidence": {
                "overall": result.confidence.overall,
                "personal": result.confidence.personal,
                "education": result.confidence.education,
                "skills": result.confidence.skills,
                "experiences": result.confidence.experiences,
            },
            "rawText": result.rawText,
            "language": result.language,
        },
    }
