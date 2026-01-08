from __future__ import annotations

from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class User(BaseModel):
    """A user record."""

    id: int = Field(..., description="User ID")
    name: str = Field(..., description="Full name")
    email: str = Field(..., description="Unique email address")
    created_at: datetime = Field(..., description="Creation timestamp (UTC)")


class UserCreateRequest(BaseModel):
    """Request payload to create a user."""

    name: str = Field(..., min_length=1, max_length=100, description="Full name")
    email: str = Field(..., min_length=3, max_length=255, description="Unique email address")


class UserUpdateRequest(BaseModel):
    """Request payload to update a user."""

    name: Optional[str] = Field(None, min_length=1, max_length=100, description="Full name")
    email: Optional[str] = Field(None, min_length=3, max_length=255, description="Unique email address")


class TaskStatus(BaseModel):
    """A task status lookup value."""

    id: int = Field(..., description="Status ID (lookup)")
    name: str = Field(..., description="Status name, e.g. 'To Do'")


class TaskStatusCreateRequest(BaseModel):
    """Request payload to create a task status.

    Note: in the provided DB schema, task_status.id is a SMALLINT PK and seeded with
    well-known values (1..3). For most apps you won't create new statuses at runtime.
    """

    id: Optional[int] = Field(
        None, ge=1, le=32767, description="Optional status id (SMALLINT). If omitted, DB must supply."
    )
    name: str = Field(..., min_length=1, max_length=50, description="Status name")


class TaskStatusUpdateRequest(BaseModel):
    """Request payload to update a task status."""

    name: Optional[str] = Field(None, min_length=1, max_length=50, description="Status name")


class Task(BaseModel):
    """A task record with joined status/assignee fields for display."""

    id: int = Field(..., description="Task ID")
    title: str = Field(..., description="Task title")
    description: Optional[str] = Field(None, description="Task description")
    status_id: int = Field(..., description="FK to task_status.id")
    status: str = Field(..., description="Status display name")
    due_date: Optional[date] = Field(None, description="Due date (local date)")
    assignee_id: Optional[int] = Field(None, description="FK to users.id (nullable)")
    assignee_name: Optional[str] = Field(None, description="Assignee name (nullable)")
    created_at: datetime = Field(..., description="Creation timestamp (UTC)")
    updated_at: datetime = Field(..., description="Last update timestamp (UTC)")


class TaskCreateRequest(BaseModel):
    """Request payload to create a task."""

    title: str = Field(..., min_length=1, max_length=200, description="Task title")
    description: Optional[str] = Field(None, description="Task description")
    status_id: int = Field(1, description="Initial status_id (defaults to 'To Do')")
    due_date: Optional[date] = Field(None, description="Due date")
    assignee_id: Optional[int] = Field(None, description="Assignee user id (nullable)")


class TaskUpdateRequest(BaseModel):
    """Request payload to update editable task fields."""

    title: Optional[str] = Field(None, min_length=1, max_length=200, description="Task title")
    description: Optional[str] = Field(None, description="Task description")
    status_id: Optional[int] = Field(None, description="New status_id")
    due_date: Optional[date] = Field(None, description="Due date")
    assignee_id: Optional[int] = Field(
        None, description="Assignee user id (nullable; set null to unassign)"
    )


class TaskListFilters(BaseModel):
    """Task filtering options."""

    status_id: Optional[int] = Field(None, description="Filter by status_id")
    assignee_id: Optional[int] = Field(None, description="Filter by assignee_id")
    due_date: Optional[date] = Field(None, description="Filter by exact due_date")
    due_before: Optional[date] = Field(None, description="Filter tasks due on/before this date")


class DashboardSummary(BaseModel):
    """High-level summary for dashboard widgets."""

    total_tasks: int = Field(..., description="Total number of tasks")
    by_status: List[dict] = Field(
        ...,
        description="Counts by status. Each item: {status_id, status, count}",
    )
    upcoming_deadlines: List[Task] = Field(
        ...,
        description="Soonest upcoming tasks with due dates (ascending).",
    )
