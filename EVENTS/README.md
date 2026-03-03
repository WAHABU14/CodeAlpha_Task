# EVENTS backend (Django)

This repository contains a Django backend with a simple events and registrations API built with Django REST Framework.

Quick start (Windows):

1. Create and activate a virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

2. Run migrations and create a superuser

```powershell
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

3. APIs
- `GET /api/events/` - list events
- `GET /api/events/<id>/` - event detail
- `POST /api/events/<id>/register/` - submit registration (auth required)
- `GET /api/registrations/` - view your registrations (auth required)
- `POST /api/registrations/<id>/cancel/` - cancel a registration (auth required)

By default this project uses SQLite for ease of setup. To use PostgreSQL, update `DATABASES` in `events_backend/settings.py` and install `psycopg2-binary`.
