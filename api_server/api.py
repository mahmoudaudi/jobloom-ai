from __future__ import annotations

from fastapi import FastAPI

from applicant_recommendation.presentation.router import router as applicant_router
from cv_parsing.presentation.router import router as cv_parser_router
from job_recommendation.presentation.router import router as job_router
from schedule_verification.presentation.router import router as schedule_router
from transcript_verification.presentation.router import router as transcript_router
from .settings import settings


app = FastAPI(title="Jobloom AI Module", version="0.1.0")


@app.get(settings.health_path)
def health() -> dict[str, bool]:
    return {"ok": True}


app.include_router(job_router)
app.include_router(applicant_router)
app.include_router(schedule_router)
app.include_router(cv_parser_router)
app.include_router(transcript_router)
