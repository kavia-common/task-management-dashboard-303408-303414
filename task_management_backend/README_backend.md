# Task Management Backend (FastAPI)

This backend exposes REST APIs for users, tasks, statuses, and a dashboard summary backed by PostgreSQL.

All routes are mounted under `/api` via `app.include_router(..., prefix="/api")`.

## Required environment variables

- `DATABASE_URL` (preferred): SQLAlchemy connection string to PostgreSQL  
  Example (matches the DB container’s `db_connection.txt`):  
  `postgresql+psycopg2://appuser:dbuser123@localhost:5000/myapp`

- `DB_URL` (fallback): if your environment uses `DB_URL` instead of `DATABASE_URL`

Optional (pool tuning):
- `DB_POOL_SIZE` (default `5`)
- `DB_MAX_OVERFLOW` (default `10`)

## Local ports / connectivity notes

- Frontend dev server: `http://localhost:3000`
- Backend API base URL (expected by the frontend `.env.example`): `http://localhost:3001`
- Database (from `task_management_database/db_connection.txt`): `postgresql://appuser:dbuser123@localhost:5000/myapp`

> Note: The backend reads `DATABASE_URL`/`DB_URL` and normalizes `postgresql://` to `postgresql+psycopg2://` automatically.

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

Assuming the backend is running locally on port `3001` (do not change preview ports):

```bash
curl -s http://localhost:3001/ | jq
curl -s http://localhost:3001/api/health/db | jq

curl -s http://localhost:3001/api/statuses | jq
curl -s http://localhost:3001/api/users | jq

curl -s "http://localhost:3001/api/tasks?limit=10" | jq
curl -s "http://localhost:3001/api/tasks?status_id=1" | jq
curl -s "http://localhost:3001/api/tasks?assignee_id=1" | jq
curl -s "http://localhost:3001/api/tasks?due_before=2026-01-31" | jq

curl -s http://localhost:3001/api/dashboard/summary | jq
```

## E2E smoke script (recommended)

A lightweight script is included to validate core flows across endpoints.

It checks:
- `/api/health/db`
- create/list/update tasks
- assign/unassign user
- filters: `assignee_id`, `status_id`, `due_before`
- `/api/dashboard/summary`

Run:

```bash
# Default base URL: http://localhost:3001
python -m src.e2e_smoke

# Or override:
E2E_API_BASE_URL=http://localhost:3001 python -m src.e2e_smoke
```

## Notes / current environment caveat

- In this workspace, direct psql connectivity to `localhost:5000` may be unavailable depending on how the DB container is networked/exposed.
  The backend is DB-ready via `DATABASE_URL`/`DB_URL`, but runtime connectivity ultimately depends on environment/container wiring.
