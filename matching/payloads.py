from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class ExperiencePayload(BaseModel):
    title: str
    company: str
    period: str = ""
    description: str = ""


class LocationPayload(BaseModel):
    country: str = ""
    city: str = ""


class StudentPayload(BaseModel):
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
    skills: List[str] = Field(default_factory=list)
    experiences: List[ExperiencePayload] = Field(default_factory=list)
    location: LocationPayload = Field(default_factory=LocationPayload)
    scheduleFileName: Optional[str] = None
    cvFileName: Optional[str] = None


class JobPayload(BaseModel):
    id: str
    title: str
    description: str = ""
    requirements: List[str] = Field(default_factory=list)
    category: str = ""
    type: str = ""
    company: str = ""
    salary: str = ""
    location: str = ""
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    schedule: str = ""
    isVerified: bool = True
    locationText: str = ""
