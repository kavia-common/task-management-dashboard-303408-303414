# Task Management Backend (FastAPI)

This backend exposes REST APIs for users, tasks, statuses, and a dashboard summary backed by PostgreSQL.

## Required environment variables

- `DATABASE_URL` (preferred): SQLAlchemy connection string to PostgreSQL  
  Example (local DB container):  
  `postgresql+psycopg2://appuser:dbuser123@localhost:5000/myapp`

- `DB_URL` (fallback): if your environment uses `DB_URL` instead of `DATABASE_URL`

Optional:
- `DB_POOL_SIZE` (default `5`)
- `DB_MAX_OVERFLOW` (default `10`)

You can copy `.env.example` to your own `.env` (do not commit secrets).

## CORS

CORS is configured to allow the local frontend dev origin:

- `http://localhost:3000`

If your frontend runs elsewhere, add the origin in `src/api/main.py`.

## OpenAPI / Docs

FastAPI’s built-in docs are available at:

- Swagger UI: `/docs`
- ReDoc: `/redoc`
- Raw OpenAPI JSON: `/openapi.json`
- Additional usage helper: `/docs/help`

All routes are mounted under `/api` via `app.include_router(..., prefix="/api")`.

## API overview

### Health
- `GET /` health check
- `GET /api/health/db` DB connectivity check (`SELECT 1`)

### Statuses
- `GET /api/statuses`
- `GET /api/statuses/{status_id}`
- `POST /api/statuses`
- `PATCH /api/statuses/{status_id}`
- `DELETE /api/statuses/{status_id}`

> Note: `task_status` is typically a fixed lookup table (seeded values 1..3). The create/update/delete endpoints are provided for completeness/dev/admin usage.

### Users
- `GET /api/users`
- `GET /api/users/{user_id}`
- `POST /api/users`
- `PATCH /api/users/{user_id}`
- `DELETE /api/users/{user_id}`

### Tasks
- `GET /api/tasks` with optional filters:
  - `status_id`
  - `assignee_id`
  - `due_date` (exact date match)
  - `due_before` (tasks with due_date <= due_before)
  - `limit`, `offset`
- `GET /api/tasks/{task_id}`
- `POST /api/tasks`
- `PATCH /api/tasks/{task_id}` (title, description, status_id, due_date, assignee_id)
- `DELETE /api/tasks/{task_id}`

### Dashboard
- `GET /api/dashboard/summary?upcoming_limit=5`

## Manual verification (smoke checks)

Assuming the backend is running locally (for example via `uvicorn src.api.main:app --reload`):

```bash
curl -s http://localhost:8000/ | jq
curl -s http://localhost:8000/api/health/db | jq

curl -s http://localhost:8000/api/statuses | jq
curl -s http://localhost:8000/api/users | jq

curl -s "http://localhost:8000/api/tasks?limit=10" | jq
curl -s "http://localhost:8000/api/tasks?status_id=1" | jq
curl -s "http://localhost:8000/api/tasks?assignee_id=1" | jq
curl -s "http://localhost:8000/api/tasks?due_before=2026-01-31" | jq

curl -s http://localhost:8000/api/dashboard/summary | jq
```

## Notes / current environment caveat

- In this workspace, direct psql connectivity to `localhost:5000` may be unavailable depending on how the DB container is networked/exposed.
  The backend is DB-ready via `DATABASE_URL`/`DB_URL`, but runtime connectivity ultimately depends on environment/container wiring.
