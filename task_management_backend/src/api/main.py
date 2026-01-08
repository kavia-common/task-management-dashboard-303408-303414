from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes import router as api_router

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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
            "statuses": "/api/statuses",
            "users": "/api/users",
            "tasks": "/api/tasks",
            "dashboard_summary": "/api/dashboard/summary",
        },
    }
