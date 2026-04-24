# Jobloom AI Module

This folder is the standalone Python AI module for Jobloom.

Current scope:
- Job recommendation for students
- Applicant recommendation for companies
- Mock data inputs + computed ranking
- Deterministic scoring from `AI_SPEC.md`

Structure:
- `job_recommendation/` student-facing job ranking feature
- `applicant_recommendation/` company-facing applicant ranking feature
- `matching/` shared student/job models and scoring formula
- `api_server/` FastAPI app + runtime settings
- `.env` runtime config for host, port, endpoint paths, and mock/real mode

The mock inputs here are copied from the mobile app's fake data layer
so the AI module can be developed independently.
The fixtures live in:
- `job_recommendation/infrastructure/mock_rank_jobs.json`
- `applicant_recommendation/infrastructure/mock_rank_students.json`

Run the API:

```bash
python __main__.py
```

Runtime config lives in `.env`:

```env
JOBLOOM_AI_DATA_SOURCE=mock
JOBLOOM_AI_RANK_JOBS_PATH=/ai/rank-jobs
JOBLOOM_AI_RANK_STUDENTS_PATH=/ai/rank-students
```

Use `JOBLOOM_AI_DATA_SOURCE=mock` while testing with local fixtures. Later, set it to `real` so empty requests stop using fixtures and the backend must send the real `student/jobs` or `job/students` payload.

Postman:

- `GET /ai/health`
- `POST /ai/rank-jobs`
- `POST /ai/rank-students`

For quick testing in `mock` mode, you can send an empty body to `POST /ai/rank-jobs` or `POST /ai/rank-students` and it will use mock data automatically.
That mock data is copied from `Jobloom mobile`, but the ranking is always calculated by the scoring engine.

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
