"""
End-to-end smoke checks for the Task Management stack.

This script is intentionally lightweight and uses only standard library + requests.

It validates the core flows against the running backend:
- DB health endpoint
- Create/list/update tasks
- Assign/unassign users
- Filter tasks by assignee/status/due_before
- Read dashboard summary

Environment variables:
- E2E_API_BASE_URL (optional): Base URL for the backend, default http://localhost:3001
  Note: backend routes are mounted under /api, so this script uses /api/* paths.

Usage:
  python -m src.e2e_smoke
or:
  E2E_API_BASE_URL=http://localhost:3001 python -m src.e2e_smoke
"""

from __future__ import annotations

import json
import os
import sys
import time
from datetime import date, timedelta
from typing import Any, Dict, Optional
from urllib.parse import urlencode

import requests


def _api_base() -> str:
    base = os.getenv("E2E_API_BASE_URL", "http://localhost:3001").strip()
    return base[:-1] if base.endswith("/") else base


# PUBLIC_INTERFACE
def run_smoke() -> int:
    """Run E2E smoke checks against the configured backend.

    Returns:
        int: process exit code (0 success, 1 failure)
    """
    base = _api_base()
    session = requests.Session()
    session.headers.update({"Accept": "application/json"})

    def url(path: str, params: Optional[Dict[str, Any]] = None) -> str:
        full = f"{base}{path}"
        if params:
            return f"{full}?{urlencode({k: v for k, v in params.items() if v is not None})}"
        return full

    def check(name: str, fn):
        try:
            print(f"[SMOKE] {name} ...", flush=True)
            fn()
            print(f"[SMOKE] {name} OK", flush=True)
        except Exception as e:
            print(f"[SMOKE] {name} FAILED: {e}", file=sys.stderr, flush=True)
            raise

    def get_json(path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        r = session.get(url(path, params=params), timeout=10)
        r.raise_for_status()
        return r.json()

    def post_json(path: str, payload: Dict[str, Any]) -> Any:
        r = session.post(url(path), json=payload, timeout=10)
        r.raise_for_status()
        return r.json()

    def patch_json(path: str, payload: Dict[str, Any]) -> Any:
        r = session.patch(url(path), json=payload, timeout=10)
        r.raise_for_status()
        return r.json()

    # ---- Checks ----

    def _db_health():
        payload = get_json("/api/health/db")
        if payload.get("ok") is not True:
            raise RuntimeError(f"DB health returned not ok: {payload}")

    def _read_statuses():
        statuses = get_json("/api/statuses")
        if not isinstance(statuses, list) or len(statuses) < 1:
            raise RuntimeError(f"Expected statuses list, got: {statuses}")
        # Ensure the standard seeded statuses exist if DB is seeded as expected
        ids = {s.get("id") for s in statuses if isinstance(s, dict)}
        if 1 not in ids:
            # Not fatal; but warn because seed expectation might be off.
            print("[SMOKE][WARN] Expected seeded status id=1 not found.", flush=True)

    def _ensure_user() -> Dict[str, Any]:
        users = get_json("/api/users")
        if isinstance(users, list) and users:
            return users[0]
        # Create a user if none exist
        created = post_json(
            "/api/users",
            {"name": f"Smoke User {int(time.time())}", "email": f"smoke{int(time.time())}@example.com"},
        )
        if "id" not in created:
            raise RuntimeError(f"Create user did not return id: {created}")
        return created

    def _task_crud_and_filters():
        user = _ensure_user()

        due = (date.today() + timedelta(days=7)).isoformat()
        task = post_json(
            "/api/tasks",
            {
                "title": f"Smoke Task {int(time.time())}",
                "description": "Created by e2e smoke test",
                "status_id": 1,
                "due_date": due,
                "assignee_id": None,
            },
        )
        task_id = task.get("id")
        if not task_id:
            raise RuntimeError(f"Create task did not return id: {task}")

        # List tasks (should include newly created)
        tasks = get_json("/api/tasks", params={"limit": 50})
        if not any(t.get("id") == task_id for t in tasks):
            raise RuntimeError("Created task not found in task list")

        # Update status
        updated = patch_json(f"/api/tasks/{task_id}", {"status_id": 2})
        if updated.get("status_id") != 2:
            raise RuntimeError(f"Expected status_id=2 after patch, got: {updated}")

        # Assign user
        updated2 = patch_json(f"/api/tasks/{task_id}", {"assignee_id": user["id"]})
        if updated2.get("assignee_id") != user["id"]:
            raise RuntimeError(f"Expected assignee_id={user['id']} after patch, got: {updated2}")

        # Filter by assignee
        by_assignee = get_json("/api/tasks", params={"assignee_id": user["id"], "limit": 50})
        if not any(t.get("id") == task_id for t in by_assignee):
            raise RuntimeError("Created task not found in assignee filter results")

        # Filter by status
        by_status = get_json("/api/tasks", params={"status_id": 2, "limit": 50})
        if not any(t.get("id") == task_id for t in by_status):
            raise RuntimeError("Created task not found in status filter results")

        # Filter by due_before
        by_due = get_json("/api/tasks", params={"due_before": due, "limit": 50})
        if not any(t.get("id") == task_id for t in by_due):
            raise RuntimeError("Created task not found in due_before filter results")

        # Unassign (nullable)
        updated3 = patch_json(f"/api/tasks/{task_id}", {"assignee_id": None})
        if updated3.get("assignee_id") is not None:
            raise RuntimeError(f"Expected assignee_id=null after unassign, got: {updated3}")

    def _dashboard_summary():
        summary = get_json("/api/dashboard/summary", params={"upcoming_limit": 5})
        if not isinstance(summary, dict) or "total_tasks" not in summary:
            raise RuntimeError(f"Unexpected dashboard summary payload: {summary}")
        if "by_status" not in summary or "upcoming_deadlines" not in summary:
            raise RuntimeError(f"Missing expected keys in summary: {summary}")

    # Execute
    check("DB health", _db_health)
    check("Statuses list", _read_statuses)
    check("Task CRUD + filters", _task_crud_and_filters)
    check("Dashboard summary", _dashboard_summary)

    print("[SMOKE] All checks passed.", flush=True)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(run_smoke())
    except Exception:
        # We already printed failure reason in check()
        sys.exit(1)
