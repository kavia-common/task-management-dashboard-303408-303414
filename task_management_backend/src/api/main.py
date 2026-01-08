from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.engine import Engine

from src.api.routes import router as api_router
from src.db import get_engine

openapi_tags = [
    {"name": "Statuses", "description": "Task status lookup endpoints."},
    {"name": "Users", "description": "User directory endpoints for task assignment."},
    {"name": "Tasks", "description": "Task CRUD + filtering endpoints."},
    {"name": "Dashboard", "description": "Summary endpoints for dashboard widgets."},
    {"name": "Health", "description": "Service health and configuration helpers."},
]

app = FastAPI(
    title="Task Management API",
    description=(
        "REST API for a task management dashboard: create tasks, assign users, "
        "update statuses, set due dates, filter lists, and fetch dashboard summaries."
    ),
    version="1.0.0",
    openapi_tags=openapi_tags,
)

# Allow local frontend dev server. Add more origins as needed for staging/prod.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")


@app.get(
    "/",
    tags=["Health"],
    summary="Health check",
    description="Simple health check endpoint.",
    operation_id="healthCheck",
)
def health_check():
    """Health check endpoint.

    Returns:
        dict: A simple message indicating the service is up.
    """
    return {"message": "Healthy"}


@app.get(
    "/api/health/db",
    tags=["Health"],
    summary="Database connectivity health check",
    description="Attempts a lightweight `SELECT 1` against the configured PostgreSQL database.",
    operation_id="healthCheckDb",
)
def health_check_db(engine: Engine = Depends(get_engine)):
    """Database health check endpoint.

    This endpoint verifies that the backend can connect to the configured database
    (via DATABASE_URL preferred; falling back to DB_URL) by executing `SELECT 1`.

    Returns:
        dict: {ok: bool, error?: str}
    """
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"ok": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@app.get(
    "/docs/help",
    tags=["Health"],
    summary="API usage help",
    description="Quick notes on required environment variables and common endpoints.",
    operation_id="docsHelp",
)
def docs_help():
    """Provide usage notes for local/dev configuration.

    Environment variables required:
      - DATABASE_URL (preferred) or DB_URL:
        postgresql+psycopg2://appuser:dbuser123@localhost:5000/myapp

    Returns:
        dict: Helpful configuration and endpoint hints.
    """
    return {
        "required_env": ["DATABASE_URL (preferred) or DB_URL"],
        "example_DATABASE_URL": "postgresql+psycopg2://appuser:dbuser123@localhost:5000/myapp",
        "base_path": "/api",
        "endpoints": {
            "db_health": "/api/health/db",
            "statuses": "/api/statuses",
            "users": "/api/users",
            "tasks": "/api/tasks",
            "dashboard_summary": "/api/dashboard/summary",
        },
    }
