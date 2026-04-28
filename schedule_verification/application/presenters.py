from __future__ import annotations

from typing import Any, Dict

from schedule_verification.domain.models import ScheduleVerification


def build_verify_schedule_response(result: ScheduleVerification) -> Dict[str, Any]:
    return {
        "success": True,
        "data": {
            "isVerified": result.isVerified,
            "confidence": result.confidence,
            "message": result.message,
            "extracted": result.extracted,
            "checks": result.checks,
            "issues": result.issues,
        },
    }
