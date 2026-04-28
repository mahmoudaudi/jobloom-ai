from __future__ import annotations

from fastapi import APIRouter, HTTPException

from api_server.settings import settings
from cv_parsing.application.dtos import ParseCvRequest, RefreshProfileSectionRequest
from cv_parsing.application.refresh_section import RefreshProfileSectionUseCase
from cv_parsing.application.use_cases import ParseCvUseCase
from cv_parsing.infrastructure.gemini_cv_extractor import build_cv_extractor


router = APIRouter()
_parse_cv_use_case = ParseCvUseCase(extractor=build_cv_extractor())
_refresh_profile_section_use_case = RefreshProfileSectionUseCase(_parse_cv_use_case)


@router.post(settings.parse_cv_path)
def parse_cv(payload: ParseCvRequest | None = None) -> dict:
    request = payload or ParseCvRequest()
    try:
        return _parse_cv_use_case.execute(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post(settings.refresh_profile_section_path)
def refresh_profile_section(payload: RefreshProfileSectionRequest) -> dict:
    try:
        return _refresh_profile_section_use_case.execute(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
