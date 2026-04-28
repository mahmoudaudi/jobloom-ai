from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class PersonalInfo:
    fullName: str = ""
    email: str = ""
    phone: str = ""
    country: str = ""
    city: str = ""


@dataclass(frozen=True)
class EducationInfo:
    degree: str = ""
    majorName: str = ""
    university: str = ""
    yearLabel: str = ""
    educationPeriod: str = ""
    expectedGraduation: str = ""
    gpa: float | None = None


@dataclass(frozen=True)
class ExperienceInfo:
    title: str = ""
    company: str = ""
    period: str = ""
    description: str = ""


@dataclass(frozen=True)
class ConfidenceInfo:
    overall: float = 0.0
    personal: float = 0.0
    education: float = 0.0
    skills: float = 0.0
    experiences: float = 0.0


@dataclass(frozen=True)
class ParsedCv:
    personal: PersonalInfo = field(default_factory=PersonalInfo)
    education: EducationInfo = field(default_factory=EducationInfo)
    skills: list[str] = field(default_factory=list)
    experiences: list[ExperienceInfo] = field(default_factory=list)
    confidence: ConfidenceInfo = field(default_factory=ConfidenceInfo)
    rawText: str | None = None
    language: str = "unknown"
