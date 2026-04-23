from __future__ import annotations

from typing import Any, Dict, Sequence

from models import Job, StudentProfile
from ranking import match_label, rank_jobs_for_student


def build_rank_jobs_response(
    student: StudentProfile,
    jobs: Sequence[Job],
    *,
    use_mock_data: bool = False,
) -> Dict[str, Any]:
    if use_mock_data:
        return {
            "success": True,
            "data": [
                {
                    "jobId": job.id,
                    "matchPercentage": job.matchPercentage,
                    "reasons": [
                        "Mock data from Jobloom mobile",
                        match_label(job.matchPercentage),
                    ],
                }
                for job in jobs
            ],
        }

    ranked = rank_jobs_for_student(student, jobs)
    return {
        "success": True,
        "data": [
            {
                "jobId": item.jobId,
                "matchPercentage": item.matchPercentage,
                "reasons": item.reasons,
            }
            for item in ranked
        ],
    }
