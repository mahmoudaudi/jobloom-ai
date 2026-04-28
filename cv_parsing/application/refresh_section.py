from __future__ import annotations

from .dtos import RefreshProfileSectionRequest
from .use_cases import ParseCvUseCase


SECTION_MESSAGES = {
    "education": "Found your education details from the latest CV.",
    "location": "Detected your location from the latest CV.",
    "phone": "Detected a phone number in the latest CV.",
    "skills": "Found skills in your latest CV.",
    "experiences": "Found experience entries in your latest CV.",
}


class RefreshProfileSectionUseCase:
    def __init__(self, parse_cv_use_case: ParseCvUseCase) -> None:
        self._parse_cv_use_case = parse_cv_use_case

    def execute(self, payload: RefreshProfileSectionRequest) -> dict:
        section = payload.section.strip().lower()
        if section not in {"education", "location", "phone", "skills", "experiences"}:
            raise ValueError("section must be one of: education, location, phone, skills, experiences")

        parsed = self._parse_cv_use_case.parse(payload)

        if section == "education":
            data = {
                "degree": parsed.education.degree,
                "majorName": parsed.education.majorName,
                "university": parsed.education.university,
                "yearLabel": parsed.education.yearLabel,
                "educationPeriod": parsed.education.educationPeriod,
                "expectedGraduation": parsed.education.expectedGraduation,
                "gpa": parsed.education.gpa,
                "confidence": parsed.confidence.education,
                "message": SECTION_MESSAGES[section],
            }
        elif section == "location":
            data = {
                "country": parsed.personal.country,
                "city": parsed.personal.city,
                "confidence": parsed.confidence.personal,
                "message": SECTION_MESSAGES[section],
            }
        elif section == "phone":
            data = {
                "phone": parsed.personal.phone,
                "confidence": parsed.confidence.personal,
                "message": SECTION_MESSAGES[section],
            }
        elif section == "skills":
            data = {
                "skills": parsed.skills,
                "confidence": parsed.confidence.skills,
                "message": SECTION_MESSAGES[section],
            }
        else:
            data = {
                "experiences": [
                    {
                        "title": item.title,
                        "company": item.company,
                        "period": item.period,
                        "description": item.description,
                    }
                    for item in parsed.experiences
                ],
                "confidence": parsed.confidence.experiences,
                "message": SECTION_MESSAGES[section],
            }

        return {"success": True, "data": data}
