from __future__ import annotations

from typing import Optional

from fastapi import FastAPI

from mock_data import get_mock_jobs, get_mock_student
from models import Experience, Job, Location, StudentProfile
from schemas import RankJobsRequest, StudentPayload, JobPayload
from service import build_rank_jobs_response


app = FastAPI(title="Jobloom AI Module", version="0.1.0")


def _to_student_profile(payload: StudentPayload) -> StudentProfile:
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
                period="",
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


def _to_job(payload: JobPayload) -> Job:
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


@app.get("/ai/health")
def health() -> dict[str, bool]:
    return {"ok": True}


@app.post("/ai/rank-jobs")
def rank_jobs(payload: Optional[RankJobsRequest] = None) -> dict:
    if payload is None or payload.useMockData or payload.student is None or not payload.jobs:
        student = get_mock_student()
        jobs = get_mock_jobs()
        return build_rank_jobs_response(student, jobs, use_mock_data=True)
    else:
        student = _to_student_profile(payload.student)
        jobs = [_to_job(job) for job in payload.jobs]
        return build_rank_jobs_response(student, jobs, use_mock_data=False)
