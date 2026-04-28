from __future__ import annotations

import sys
from pathlib import Path

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from api_server.api import app


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    client = TestClient(app)

    health = client.get("/ai/health")
    assert_true(health.status_code == 200, "health endpoint failed")
    assert_true(health.json() == {"ok": True}, "health response shape changed")

    rank_jobs = client.post("/ai/rank-jobs", json={})
    rank_jobs_body = rank_jobs.json()
    assert_true(rank_jobs.status_code == 200, "rank-jobs endpoint failed")
    assert_true(rank_jobs_body.get("success") is True, "rank-jobs success flag missing")
    assert_true(bool(rank_jobs_body.get("data")), "rank-jobs returned no rows")
    assert_true(
        {"jobId", "matchPercentage", "reasons"} <= set(rank_jobs_body["data"][0]),
        "rank-jobs row shape changed",
    )

    rank_students = client.post("/ai/rank-students", json={})
    rank_students_body = rank_students.json()
    assert_true(rank_students.status_code == 200, "rank-students endpoint failed")
    assert_true(rank_students_body.get("success") is True, "rank-students success flag missing")
    assert_true(bool(rank_students_body.get("data")), "rank-students returned no rows")
    assert_true(
        {"studentId", "matchPercentage", "matchReasons"} <= set(rank_students_body["data"][0]),
        "rank-students row shape changed",
    )

    verify_schedule = client.post("/ai/verify-schedule", json={})
    verify_schedule_body = verify_schedule.json()
    assert_true(verify_schedule.status_code == 200, "verify-schedule endpoint failed")
    assert_true(
        verify_schedule_body.get("success") is True,
        "verify-schedule success flag missing",
    )
    assert_true(
        {"isVerified", "confidence", "checks"} <= set(verify_schedule_body["data"]),
        "verify-schedule data shape changed",
    )

    verify_transcript = client.post("/ai/verify-transcript", json={})
    verify_transcript_body = verify_transcript.json()
    assert_true(verify_transcript.status_code == 200, "verify-transcript endpoint failed")
    assert_true(
        verify_transcript_body.get("success") is True,
        "verify-transcript success flag missing",
    )
    assert_true(
        {"isVerified", "confidence", "checks"} <= set(verify_transcript_body["data"]),
        "verify-transcript data shape changed",
    )

    real_jobs_error = client.post("/ai/rank-jobs", json={"useMockData": False})
    assert_true(real_jobs_error.status_code == 400, "rank-jobs should require real payload")

    real_students_error = client.post("/ai/rank-students", json={"useMockData": False})
    assert_true(real_students_error.status_code == 400, "rank-students should require real payload")

    real_schedule_error = client.post("/ai/verify-schedule", json={"useMockData": False})
    assert_true(
        real_schedule_error.status_code == 400,
        "verify-schedule should require real payload",
    )
    real_transcript_error = client.post("/ai/verify-transcript", json={"useMockData": False})
    assert_true(
        real_transcript_error.status_code == 400,
        "verify-transcript should require real payload",
    )
    real_cv_error = client.post("/ai/parse-cv", json={"useMockData": False})
    assert_true(real_cv_error.status_code == 400, "parse-cv should require a file reference")
    mock_cv_error = client.post("/ai/parse-cv", json={"useMockData": True})
    assert_true(mock_cv_error.status_code == 400, "parse-cv should reject mock mode")
    refresh_skills_error = client.post(
        "/ai/suggest-profile-section",
        json={"useMockData": True, "section": "skills"},
    )
    assert_true(
        refresh_skills_error.status_code == 400,
        "refresh-profile-section should reject mock mode",
    )
    bad_section_error = client.post(
        "/ai/suggest-profile-section",
        json={"section": "bad-section"},
    )
    assert_true(bad_section_error.status_code == 400, "refresh-profile-section should reject unknown section")

    print("AI module smoke test: PASS")
    print(f"rank-jobs first row: {rank_jobs_body['data'][0]}")
    print(f"rank-students first row: {rank_students_body['data'][0]}")
    print(f"verify-schedule data: {verify_schedule_body['data']}")
    print(f"verify-transcript data: {verify_transcript_body['data']}")


if __name__ == "__main__":
    main()
