# Jobloom AI Module

This folder is the standalone Python AI module for Jobloom.

Current scope:
- Job recommendation for students
- Mock data only
- Deterministic scoring from `AI_SPEC.md`

The mock inputs here are copied from the mobile app's fake data layer
so the AI module can be developed independently.

Run the API:

```bash
uvicorn app:app --reload
```

Postman:

- `GET /ai/health`
- `POST /ai/rank-jobs`

For quick testing, you can send an empty body to `POST /ai/rank-jobs` and it will use mock data automatically.
That mock data is copied from `Jobloom mobile` and returns the same job cards/scores used in the app demo.

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
