# Smart Parking (Django)

A Django 4.2 application for managing parking lots, parking spaces, clients, and reservations with availability checks and occupancy tracking.

## Features
- CRUD flows for clients, parking lots, parking spaces, and reservations (UI + Django admin).
- Prevents overlapping bookings, auto-numbers reservations, and calculates costs from duration.
- Occupancy sync service (`refresh_parking_state`) keeps spaces and lots marked open/full.
- Bootstrap 5 UI with crispy-forms; authenticated dashboard plus public landing pages.

## Tech stack
- Python 3.12, Django 4.2, crispy-bootstrap5, django-environ, Whitenoise.
- SQLite by default; override via `DATABASE_URL` for Postgres or other backends.
- pytest + pytest-django; black, isort, flake8 for formatting/linting.

## Quickstart
1) Python env: `python -m venv .venv` then `.\.venv\Scripts\activate` (Windows) or `source .venv/bin/activate` (macOS/Linux).
2) Install deps: `pip install -r requirements-dev.txt`.
3) Configure env: copy `.env.example` to `.env` (`copy .env.example .env` on Windows or `cp .env.example .env` on Unix) and set values (`SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, etc.).
4) Database: `python manage.py migrate`.
5) (Optional) Admin user: `python manage.py createsuperuser`.
6) Run server: `python manage.py runserver` (defaults to `bloger.settings.development`).

## Running tests
- `pytest`
- Coverage: `pytest --cov=blog --cov-report=term-missing`

## Key environment variables
- `DJANGO_SETTINGS_MODULE` (e.g., `bloger.settings.development`, `bloger.settings.production`)
- `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`
- `DATABASE_URL` (e.g., `sqlite:///db.sqlite3`, `postgres://user:pass@host:5432/dbname`)
- `ADMINS`, `DEFAULT_FROM_EMAIL`
- `CACHE_URL` (optional; falls back to locmem)
- `ENABLE_DEBUG_TOOLBAR` (local only)
- `SENTRY_DSN`, `SENTRY_TRACES_SAMPLE_RATE`, `SECURE_HSTS_SECONDS` (production)

## Static & media
- Local: static files in `static/`; uploads in `media/`.
- Production: set `DJANGO_SETTINGS_MODULE=bloger.settings.production`, run `python manage.py collectstatic`, and Whitenoise serves assets.

## Useful URLs
- Admin: `/admin/`
- App pages: `/dashboard/`, `/client/`, `/parking_lot/`, `/parking_space/`, `/reservation/`, plus supporting login/signup routes.
