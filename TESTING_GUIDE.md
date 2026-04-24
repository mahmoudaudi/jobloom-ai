# Jobloom AI Testing Guide

## 1) Start

```powershell
cd C:\Users\maaud\Desktop\ai_module
python __main__.py
```

The server reads `.env` on startup:

```env
JOBLOOM_AI_DATA_SOURCE=mock
JOBLOOM_AI_RANK_JOBS_PATH=/ai/rank-jobs
JOBLOOM_AI_RANK_STUDENTS_PATH=/ai/rank-students
```

Use `mock` for fixture-based testing. Use `real` when the backend is ready to send actual payloads.

## 2) Endpoints

| Method | URL |
|---|---|
| GET | `http://127.0.0.1:8000/ai/health` |
| POST | `http://127.0.0.1:8000/ai/rank-jobs` |
| POST | `http://127.0.0.1:8000/ai/rank-students` |

Header for `POST`:

```text
Content-Type: application/json
```

## 3) Mock Test

The job recommendation mock fixture is stored in `job_recommendation/infrastructure/mock_rank_jobs.json`.

```json
{
  "useMockData": true
}
```

For applicant recommendations, use the same body with:

```text
POST http://127.0.0.1:8000/ai/rank-students
```

That endpoint reads `applicant_recommendation/infrastructure/mock_rank_students.json`.

## 4) Custom Test

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
        "period": "Jun 2024 - Aug 2024",
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

## 5) High Score Test

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
        "period": "Jun 2024 - Aug 2024",
        "description": "Built UI components in React and TypeScript."
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
      "title": "Frontend Intern",
      "description": "Built UI components in React and TypeScript for web projects.",
      "requirements": ["React", "TypeScript", "Git"],
      "category": "IT",
      "type": "On Site",
      "locationText": "Jeddah, Saudi Arabia"
    }
  ]
}
```

## 6) Applicant Recommendation Custom Test

```json
{
  "useMockData": false,
  "job": {
    "id": "1",
    "title": "Frontend Intern",
    "description": "Build React and TypeScript UI components.",
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
          "period": "Jun 2024 - Aug 2024",
          "description": "Built UI components in React and TypeScript."
        }
      ],
      "location": {
        "country": "Saudi Arabia",
        "city": "Jeddah"
      }
    },
    {
      "id": "2",
      "major": "Graphic Design",
      "fullName": "Emily Chen",
      "skills": ["Figma", "UI Design"],
      "experiences": [],
      "location": {
        "country": "Saudi Arabia",
        "city": "Jeddah"
      }
    }
  ]
}
```
