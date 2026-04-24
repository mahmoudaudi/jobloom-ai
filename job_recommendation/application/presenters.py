from __future__ import annotations

from typing import Any, Dict, Sequence

from job_recommendation.domain.models import RankedJob


def build_rank_jobs_response(ranked_jobs: Sequence[RankedJob]) -> Dict[str, Any]:
    return {
        "success": True,
        "data": [
            {
                "jobId": item.jobId,
                "matchPercentage": item.matchPercentage,
                "reasons": item.reasons,
            }
            for item in ranked_jobs
        ],
    }
