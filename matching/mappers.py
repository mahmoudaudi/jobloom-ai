from __future__ import annotations

from .models import Experience, Job, Location, StudentProfile
from .payloads import JobPayload, StudentPayload


def to_student_profile(payload: StudentPayload) -> StudentProfile:
    return StudentProfile(
        id=payload.id,
        major=payload.major,
        fullName=payload.fullName,
        email=payload.email,
        appliedCount=payload.appliedCount,
        interviewsCount=payload.interviewsCount,
        offersCount=payload.offersCount,
        degree=payload.degree,
        university=payload.university,
        yearLabel=payload.yearLabel,
        educationPeriod=payload.educationPeriod,
        expectedGraduation=payload.expectedGraduation,
        gpa=payload.gpa,
        country=payload.country,
        city=payload.city,
        phone=payload.phone,
        skills=list(payload.skills),
        experiences=[
            Experience(
                title=item.title,
                company=item.company,
                period=item.period,
                description=item.description,
            )
            for item in payload.experiences
        ],
        location=Location(
            country=payload.location.country,
            city=payload.location.city,
        ),
        scheduleFileName=payload.scheduleFileName,
        cvFileName=payload.cvFileName,
    )


def to_job(payload: JobPayload) -> Job:
    return Job(
        id=payload.id,
        title=payload.title,
        description=payload.description,
        requirements=list(payload.requirements),
        category=payload.category,
        type=payload.type,
        company=payload.company,
        salary=payload.salary,
        location=payload.locationText or payload.location,
        latitude=payload.latitude,
        longitude=payload.longitude,
        schedule=payload.schedule,
        isVerified=payload.isVerified,
    )


def student_from_raw(raw: dict) -> StudentProfile:
    return StudentProfile(
        id=raw["id"],
        major=raw["major"],
        fullName=raw.get("fullName", ""),
        email=raw.get("email", ""),
        appliedCount=raw.get("appliedCount", 0),
        interviewsCount=raw.get("interviewsCount", 0),
        offersCount=raw.get("offersCount", 0),
        degree=raw.get("degree", ""),
        university=raw.get("university", ""),
        yearLabel=raw.get("yearLabel", ""),
        educationPeriod=raw.get("educationPeriod", ""),
        expectedGraduation=raw.get("expectedGraduation", ""),
        gpa=raw.get("gpa"),
        country=raw.get("country", ""),
        city=raw.get("city", ""),
        phone=raw.get("phone", ""),
        skills=list(raw.get("skills", [])),
        experiences=[
            Experience(
                title=item.get("title", ""),
                company=item.get("company", ""),
                period=item.get("period", ""),
                description=item.get("description", ""),
            )
            for item in raw.get("experiences", [])
        ],
        location=Location(
            country=raw.get("location", {}).get("country", ""),
            city=raw.get("location", {}).get("city", ""),
        ),
        scheduleFileName=raw.get("scheduleFileName"),
        cvFileName=raw.get("cvFileName"),
    )


def job_from_raw(raw: dict) -> Job:
    return Job(
        id=raw["id"],
        title=raw["title"],
        description=raw.get("description", ""),
        requirements=list(raw.get("requirements", [])),
        category=raw.get("category", ""),
        type=raw.get("type", ""),
        company=raw.get("company", ""),
        salary=raw.get("salary", ""),
        location=raw.get("locationText") or raw.get("location", ""),
        latitude=raw.get("latitude"),
        longitude=raw.get("longitude"),
        schedule=raw.get("schedule", ""),
        isVerified=raw.get("isVerified", True),
    )
