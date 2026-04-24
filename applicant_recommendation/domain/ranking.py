from __future__ import annotations

from typing import List, Sequence

from matching.models import Job, StudentProfile
from matching.scoring import score_job_match
from .models import RankedStudent


def rank_students_for_job(
    job: Job,
    students: Sequence[StudentProfile],
    limit: int = 20,
) -> List[RankedStudent]:
    ranked = []
    for student in students:
        match_percentage, reasons = score_job_match(student, job)
        ranked.append(
            RankedStudent(
                studentId=student.id,
                matchPercentage=match_percentage,
                matchReasons=reasons,
            )
        )
    ranked.sort(key=lambda item: item.matchPercentage, reverse=True)
    return ranked[:limit]
