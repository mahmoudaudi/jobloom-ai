from __future__ import annotations

from typing import Any

from transcript_verification.domain.models import TranscriptVerification


def build_verify_transcript_response(result: TranscriptVerification) -> dict[str, Any]:
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

