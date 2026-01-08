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

## OpenAPI / Docs

FastAPI’s built-in docs are available at:

- Swagger UI: `/docs`
- ReDoc: `/redoc`
- Raw OpenAPI JSON: `/openapi.json`

## Manual verification (smoke checks)

Assuming the backend is running locally (for example via `uvicorn src.api.main:app --reload`):

### Health endpoints
- `GET /`  
  Expected: `{"message":"Healthy"}`

- `GET /api/health/db`  
  Expected when DB is reachable: `{"ok": true}`  
  Expected when DB is not reachable/misconfigured: `{"ok": false, "error": "..."}`

### Sample API endpoints
- `GET /api/statuses`
- `GET /api/users`
- `GET /api/tasks`
- `GET /api/dashboard/summary`

Example curl commands:
```bash
curl -s http://localhost:8000/ | jq
curl -s http://localhost:8000/api/health/db | jq
curl -s http://localhost:8000/api/statuses | jq
curl -s http://localhost:8000/api/users | jq
curl -s "http://localhost:8000/api/tasks?limit=10" | jq
curl -s http://localhost:8000/api/dashboard/summary | jq
```

## Notes / follow-ups needed

- In this environment, `DATABASE_URL`/`DB_URL` were not set at runtime during implementation, so `/api/health/db` will return `ok:false` until one of those env vars is provided.
- Routes are registered under `/api` via `src/api/main.py` -> `app.include_router(api_router, prefix="/api")`, and endpoints exist for:
  - `/api/users`
  - `/api/tasks`
  - `/api/statuses`
  - `/api/dashboard/summary`
  - `/api/health/db`
