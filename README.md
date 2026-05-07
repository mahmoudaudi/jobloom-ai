# Jobloom AI Module

This folder is the standalone Python AI module for Jobloom.

Current scope:
- CV parsing for student profiles
- Transcript verification for student transcripts
- Job recommendation for students
- Applicant recommendation for companies
- Mock data inputs + computed ranking

Structure:
- `cv_parsing/` CV parsing feature for profile prefill
- `transcript_verification/` student transcript verification feature
- `job_recommendation/` student-facing job ranking feature
- `applicant_recommendation/` company-facing applicant ranking feature
- `matching/` shared student/job models and scoring formula
- `api_server/` FastAPI app + runtime settings
- `.env` runtime config for host, port, endpoint paths, and mock/real mode

The mock inputs here are copied from the mobile app's fake data layer
so the AI module can be developed independently.
The fixtures live in:
- `cv_parsing/infrastructure/mock_parse_cv.json`
- `transcript_verification/infrastructure/mock_verify_transcript.json`
- `job_recommendation/infrastructure/mock_rank_jobs.json`
- `applicant_recommendation/infrastructure/mock_rank_students.json`

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
- `POST /ai/parse-cv`
- `POST /ai/verify-transcript`
- `POST /ai/rank-jobs`
- `POST /ai/rank-students`

For quick testing, send `"useMockData": true` to `POST /ai/verify-transcript`, `POST /ai/rank-jobs`, or `POST /ai/rank-students`.
If `JOBLOOM_AI_DATA_SOURCE=mock`, omitted payload data also falls back to mock data automatically.
That mock data is copied from `Jobloom mobile`, but the ranking is always calculated by the scoring engine.

`/ai/parse-cv` accepts a CV file reference and returns structured personal data, education fields, cleaned skills, experience entries, confidence scores, and optional raw text.

`/ai/verify-transcript` accepts transcript evidence as PDF/image metadata and returns `isVerified: true/false` with extracted fields, verification checks, and issues. It uses local extraction first, then looks for strong proof such as a verification URL or PDF digital signature when available.

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
The default CV parsing mock response is loaded from `cv_parsing/infrastructure/mock_parse_cv.json`.
The default transcript verification mock response is loaded from `transcript_verification/infrastructure/mock_verify_transcript.json`.
