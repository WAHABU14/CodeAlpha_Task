Job Platform Backend (Django)

Quick start

1. Create a virtualenv and install dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

2. Run migrations and start server:

```powershell
python manage.py migrate
python manage.py runserver
```

3. API endpoints (development):
- `POST /api/employers/` create employer (or use admin)
- `POST /api/jobs/` create a job listing (employer authenticated)
- `GET /api/jobs/` list jobs
- `GET /api/jobs/search/?q=...&location=...&min_salary=...` search jobs
- `POST /api/resumes/` upload resume (file)
- `POST /api/applications/` apply for a job
- `GET /api/applications/` list applications (filterable)

Notes
- Uses SQLite by default.
- Email backend prints to console for notifications in dev.
- Admin panel available at `/admin/`.
