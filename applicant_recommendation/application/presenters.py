from __future__ import annotations

from typing import Any, Dict, Sequence

from applicant_recommendation.domain.models import RankedStudent


def build_rank_students_response(ranked_students: Sequence[RankedStudent]) -> Dict[str, Any]:
    return {
        "success": True,
        "data": [
            {
                "studentId": item.studentId,
                "matchPercentage": item.matchPercentage,
                "matchReasons": item.matchReasons,
            }
            for item in ranked_students
        ],
    }
