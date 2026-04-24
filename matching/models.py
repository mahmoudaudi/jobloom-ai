from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass(frozen=True)
class Experience:
    title: str
    company: str
    period: str = ""
    description: str = ""


@dataclass(frozen=True)
class Location:
    country: str = ""
    city: str = ""


@dataclass(frozen=True)
class StudentProfile:
    id: str
    major: str
    fullName: str = ""
    email: str = ""
    appliedCount: int = 0
    interviewsCount: int = 0
    offersCount: int = 0
    degree: str = ""
    university: str = ""
    yearLabel: str = ""
    educationPeriod: str = ""
    expectedGraduation: str = ""
    gpa: Optional[float] = None
    country: str = ""
    city: str = ""
    phone: str = ""
    skills: List[str] = field(default_factory=list)
    experiences: List[Experience] = field(default_factory=list)
    location: Location = field(default_factory=Location)
    scheduleFileName: Optional[str] = None
    cvFileName: Optional[str] = None


@dataclass(frozen=True)
class Job:
    id: str
    title: str
    description: str
    requirements: List[str]
    category: str
    type: str
    company: str = ""
    salary: str = ""
    location: str = ""
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    schedule: str = ""
    isVerified: bool = True

    @property
    def locationText(self) -> str:
        return self.location
