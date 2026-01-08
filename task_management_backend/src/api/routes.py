from __future__ import annotations

from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.engine import Engine

from src.db import get_engine
from src.api.repository import Repository
from src.api.schemas import (
    DashboardSummary,
    Task,
    TaskCreateRequest,
    TaskStatus,
    TaskUpdateRequest,
    User,
)

router = APIRouter()


def _get_repo(engine: Engine = Depends(get_engine)) -> Repository:
    return Repository(engine)


@router.get(
    "/statuses",
    response_model=List[TaskStatus],
    tags=["Statuses"],
    summary="List task statuses",
    description="Returns the task_status lookup table (e.g. To Do, In Progress, Done).",
    operation_id="listStatuses",
)
def list_statuses(repo: Repository = Depends(_get_repo)):
    """List available task statuses."""
    return repo.list_statuses()


@router.get(
    "/users",
    response_model=List[User],
    tags=["Users"],
    summary="List users",
    description="Returns all users that tasks can be assigned to.",
    operation_id="listUsers",
)
def list_users(repo: Repository = Depends(_get_repo)):
    """List users."""
    return repo.list_users()


@router.get(
    "/tasks",
    response_model=List[Task],
    tags=["Tasks"],
    summary="List tasks",
    description="List tasks with optional filtering by status, assignee, and due date.",
    operation_id="listTasks",
)
def list_tasks(
    status_id: Optional[int] = Query(None, description="Filter by status_id"),
    assignee_id: Optional[int] = Query(None, description="Filter by assignee_id"),
    due_before: Optional[date] = Query(None, description="Filter by due date <= due_before"),
    limit: int = Query(200, ge=1, le=500, description="Max number of tasks to return"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    repo: Repository = Depends(_get_repo),
):
    """List tasks with optional filters."""
    return repo.list_tasks(
        status_id=status_id,
        assignee_id=assignee_id,
        due_before=due_before,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/tasks/{task_id}",
    response_model=Task,
    tags=["Tasks"],
    summary="Get task",
    description="Get a single task by id.",
    operation_id="getTask",
)
def get_task(task_id: int, repo: Repository = Depends(_get_repo)):
    """Get a task by id."""
    task = repo.get_task(task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return task


@router.post(
    "/tasks",
    response_model=Task,
    status_code=status.HTTP_201_CREATED,
    tags=["Tasks"],
    summary="Create task",
    description="Create a new task with title, optional description, status, due date, and assignee.",
    operation_id="createTask",
)
def create_task(payload: TaskCreateRequest, repo: Repository = Depends(_get_repo)):
    """Create a task."""
    try:
        return repo.create_task(payload.model_dump())
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not create task: {e}") from e


@router.patch(
    "/tasks/{task_id}",
    response_model=Task,
    tags=["Tasks"],
    summary="Update task",
    description="Update editable task fields (title, description, status_id, due_date, assignee_id).",
    operation_id="updateTask",
)
def update_task(task_id: int, payload: TaskUpdateRequest, repo: Repository = Depends(_get_repo)):
    """Update a task."""
    patch = {k: v for k, v in payload.model_dump().items() if v is not None}
    try:
        updated = repo.update_task(task_id, patch)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not update task: {e}") from e

    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return updated


@router.delete(
    "/tasks/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Tasks"],
    summary="Delete task",
    description="Delete a task by id.",
    operation_id="deleteTask",
)
def delete_task(task_id: int, repo: Repository = Depends(_get_repo)):
    """Delete a task."""
    ok = repo.delete_task(task_id)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return None


@router.get(
    "/dashboard/summary",
    response_model=DashboardSummary,
    tags=["Dashboard"],
    summary="Dashboard summary",
    description="Returns counts by status plus upcoming deadline tasks.",
    operation_id="getDashboardSummary",
)
def dashboard_summary(
    upcoming_limit: int = Query(5, ge=1, le=20, description="Number of upcoming deadlines to return"),
    repo: Repository = Depends(_get_repo),
):
    """Get dashboard summary widgets data."""
    return repo.dashboard_summary(upcoming_limit=upcoming_limit)
