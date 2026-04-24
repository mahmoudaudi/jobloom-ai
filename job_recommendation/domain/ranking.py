from __future__ import annotations

from typing import List, Sequence

from matching.models import Job, StudentProfile
from matching.scoring import score_job_match
from .models import RankedJob


def rank_jobs_for_student(student: StudentProfile, jobs: Sequence[Job]) -> List[RankedJob]:
    ranked = []
    for job in jobs:
        match_percentage, reasons = score_job_match(student, job)
        ranked.append(
            RankedJob(
                jobId=job.id,
                matchPercentage=match_percentage,
                reasons=reasons,
            )
        )
    ranked.sort(key=lambda item: item.matchPercentage, reverse=True)
    return ranked
