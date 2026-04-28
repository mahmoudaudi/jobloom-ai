# Jobloom AI Module

This folder is the standalone Python AI module for Jobloom.

Current scope:
- Job recommendation for students
- Applicant recommendation for companies
- Schedule verification for student schedule PDFs
- Mock data inputs + computed ranking

Structure:
- `job_recommendation/` student-facing job ranking feature
- `applicant_recommendation/` company-facing applicant ranking feature
- `schedule_verification/` student schedule verification feature
- `matching/` shared student/job models and scoring formula
- `api_server/` FastAPI app + runtime settings
- `.env` runtime config for host, port, endpoint paths, and mock/real mode

The mock inputs here are copied from the mobile app's fake data layer
so the AI module can be developed independently.
The fixtures live in:
- `job_recommendation/infrastructure/mock_rank_jobs.json`
- `applicant_recommendation/infrastructure/mock_rank_students.json`
- `schedule_verification/infrastructure/mock_verify_schedule.json`

Run the API:

```bash
python __main__.py
```

Run a quick smoke test:

```bash
python scripts/smoke_test.py
```

Check whether the deterministic ranking module is light, medium, or heavy:

```bash
python scripts/load_profile.py
```

Use `JOBLOOM_AI_DATA_SOURCE=mock` while testing with local fixtures. Later, set it to `real` so empty requests stop using fixtures and the backend must send the real `student/jobs` or `job/students` payload.

Postman:

- `GET /ai/health`
- `POST /ai/rank-jobs`
- `POST /ai/rank-students`
- `POST /ai/verify-schedule`

For quick testing in `mock` mode, you can send an empty body to `POST /ai/rank-jobs`, `POST /ai/rank-students`, or `POST /ai/verify-schedule` and it will use mock data automatically.
That mock data is copied from `Jobloom mobile`, but the ranking is always calculated by the scoring engine.

`/ai/verify-schedule` accepts schedule evidence as either PDF or image metadata (`application/pdf`, `image/png`, `image/jpeg`, `image/webp`). The verifier checks the extracted schedule information: student name, university, current semester, and courses.

For real file extraction, send `filePath` or `fileUrl` inside `schedule`; the verifier now tries local extraction first:
- PDF text extraction via `PyMuPDF`
- OCR for scanned PDFs/images via `pytesseract`
- local rules for semester/course detection and schedule classification

If local extraction is incomplete and Gemini is configured, the verifier falls back to Gemini automatically. To enable that fallback, set `JOBLOOM_AI_LLM_PROVIDER=gemini` and provide `JOBLOOM_AI_GEMINI_API_KEY`.

OCR note:
- `pytesseract` requires the native Tesseract OCR binary to be installed and available in `PATH`.

If you want to test with custom data, send:

```json
{
  "useMockData": false,
  "student": {
    "id": "1",
    "major": "Computer Science",
    "skills": ["React", "TypeScript", "Git"],
    "experiences": [
      {
        "title": "Frontend Intern",
        "company": "ABC Tech",
        "description": "Built UI components in React."
      }
    ],
    "location": {
      "country": "Saudi Arabia",
      "city": "Jeddah"
    },
    "yearLabel": "Year 3 of 4",
    "gpa": 3.8
  },
  "jobs": [
    {
      "id": "1",
      "title": "Frontend Developer Intern",
      "description": "Work on web projects.",
      "requirements": ["React", "TypeScript", "Git"],
      "category": "IT",
      "type": "Remote",
      "locationText": ""
    }
  ]
}
```

Applicant recommendation custom test:

```json
{
  "useMockData": false,
  "job": {
    "id": "1",
    "title": "Frontend Developer Intern",
    "description": "Work on web projects.",
    "requirements": ["React", "TypeScript", "Git"],
    "category": "IT",
    "type": "On Site",
    "locationText": "Jeddah, Saudi Arabia"
  },
  "students": [
    {
      "id": "1",
      "major": "Computer Science",
      "fullName": "Alex Student",
      "skills": ["React", "TypeScript", "Git"],
      "experiences": [
        {
          "title": "Frontend Intern",
          "company": "ABC Tech",
          "description": "Built UI components in React."
        }
      ],
      "location": {
        "country": "Saudi Arabia",
        "city": "Jeddah"
      }
    }
  ]
}
```

The default job recommendation mock response is loaded from `job_recommendation/infrastructure/mock_rank_jobs.json`.
The default applicant recommendation mock response is loaded from `applicant_recommendation/infrastructure/mock_rank_students.json`.
