from __future__ import annotations

import sys
from pathlib import Path
from time import perf_counter

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from applicant_recommendation.domain.ranking import rank_students_for_job
from job_recommendation.domain.ranking import rank_jobs_for_student
from matching.models import Job, Location, StudentProfile


def build_jobs(count: int) -> list[Job]:
    return [
        Job(
            id=f"job-{index}",
            title="Frontend Developer Intern" if index % 2 == 0 else "Content Writer",
            description="Build React and TypeScript UI components.",
            requirements=["React", "TypeScript", "Git"] if index % 2 == 0 else ["Writing", "SEO"],
            category="IT" if index % 2 == 0 else "Marketing",
            type="Remote" if index % 3 == 0 else "On Site",
            location="Jeddah, Saudi Arabia",
        )
        for index in range(count)
    ]


def build_students(count: int) -> list[StudentProfile]:
    return [
        StudentProfile(
            id=f"student-{index}",
            major="Computer Science" if index % 2 == 0 else "Marketing",
            skills=["React", "TypeScript", "Git"] if index % 2 == 0 else ["Writing", "SEO"],
            location=Location(country="Saudi Arabia", city="Jeddah"),
        )
        for index in range(count)
    ]


def classify(elapsed_seconds: float) -> str:
    if elapsed_seconds < 0.25:
        return "light"
    if elapsed_seconds < 1.0:
        return "medium"
    return "heavy"


def profile_job_recommendation(candidate_count: int) -> tuple[float, int]:
    student = build_students(1)[0]
    started_at = perf_counter()
    ranked = rank_jobs_for_student(student, build_jobs(candidate_count))
    return perf_counter() - started_at, len(ranked)


def profile_applicant_recommendation(candidate_count: int) -> tuple[float, int]:
    job = build_jobs(1)[0]
    started_at = perf_counter()
    ranked = rank_students_for_job(job, build_students(candidate_count))
    return perf_counter() - started_at, len(ranked)


def main() -> None:
    candidate_count = 500
    job_elapsed, ranked_jobs = profile_job_recommendation(candidate_count)
    applicant_elapsed, ranked_students = profile_applicant_recommendation(candidate_count)

    print("Jobloom AI load profile")
    print(f"rank-jobs: ranked {ranked_jobs}/{candidate_count} in {job_elapsed:.4f}s ({classify(job_elapsed)})")
    print(
        f"rank-students: ranked top {ranked_students}/{candidate_count} "
        f"in {applicant_elapsed:.4f}s ({classify(applicant_elapsed)})"
    )


if __name__ == "__main__":
    main()
