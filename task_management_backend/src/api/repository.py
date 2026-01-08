from __future__ import annotations

from datetime import date
from typing import Any, Dict, List, Optional

from sqlalchemy import text
from sqlalchemy.engine import Engine


class Repository:
    """Thin repository that uses parameterized SQL to access the task management schema."""

    def __init__(self, engine: Engine):
        self._engine = engine

    def list_statuses(self) -> List[Dict[str, Any]]:
        with self._engine.connect() as conn:
            rows = conn.execute(text("SELECT id, name FROM task_status ORDER BY id")).mappings().all()
            return [dict(r) for r in rows]

    def get_status(self, status_id: int) -> Optional[Dict[str, Any]]:
        with self._engine.connect() as conn:
            row = conn.execute(
                text("SELECT id, name FROM task_status WHERE id = :id"),
                {"id": status_id},
            ).mappings().first()
            return dict(row) if row else None

    def create_status(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        # task_status.id is SMALLINT PK but not necessarily SERIAL; allow client-specified id or rely on DB default.
        # If id is omitted, insert only name.
        if payload.get("id") is None:
            sql = "INSERT INTO task_status (name) VALUES (:name) RETURNING id"
            params = {"name": payload.get("name")}
        else:
            sql = "INSERT INTO task_status (id, name) VALUES (:id, :name) RETURNING id"
            params = {"id": payload.get("id"), "name": payload.get("name")}

        with self._engine.begin() as conn:
            new_id = conn.execute(text(sql), params).scalar_one()

        status_row = self.get_status(int(new_id))
        if not status_row:
            raise RuntimeError("Status created but could not be reloaded")
        return status_row

    def update_status(self, status_id: int, patch: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        allowed = {"name"}
        set_parts = []
        params: Dict[str, Any] = {"id": status_id}

        for k, v in patch.items():
            if k not in allowed:
                continue
            set_parts.append(f"{k} = :{k}")
            params[k] = v

        if not set_parts:
            return self.get_status(status_id)

        sql = f"UPDATE task_status SET {', '.join(set_parts)} WHERE id = :id"
        with self._engine.begin() as conn:
            result = conn.execute(text(sql), params)
            if result.rowcount == 0:
                return None

        return self.get_status(status_id)

    def delete_status(self, status_id: int) -> bool:
        with self._engine.begin() as conn:
            result = conn.execute(text("DELETE FROM task_status WHERE id = :id"), {"id": status_id})
            return result.rowcount > 0

    def list_users(self) -> List[Dict[str, Any]]:
        with self._engine.connect() as conn:
            rows = conn.execute(
                text("SELECT id, name, email, created_at FROM users ORDER BY id")
            ).mappings().all()
            return [dict(r) for r in rows]

    def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        with self._engine.connect() as conn:
            row = conn.execute(
                text("SELECT id, name, email, created_at FROM users WHERE id = :id"),
                {"id": user_id},
            ).mappings().first()
            return dict(row) if row else None

    def create_user(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        sql = """
        INSERT INTO users (name, email)
        VALUES (:name, :email)
        RETURNING id
        """
        with self._engine.begin() as conn:
            new_id = conn.execute(text(sql), payload).scalar_one()

        user = self.get_user(int(new_id))
        if not user:
            raise RuntimeError("User created but could not be reloaded")
        return user

    def update_user(self, user_id: int, patch: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        allowed = {"name", "email"}
        set_parts = []
        params: Dict[str, Any] = {"id": user_id}

        for k, v in patch.items():
            if k not in allowed:
                continue
            set_parts.append(f"{k} = :{k}")
            params[k] = v

        if not set_parts:
            return self.get_user(user_id)

        sql = f"UPDATE users SET {', '.join(set_parts)} WHERE id = :id"
        with self._engine.begin() as conn:
            result = conn.execute(text(sql), params)
            if result.rowcount == 0:
                return None

        return self.get_user(user_id)

    def delete_user(self, user_id: int) -> bool:
        with self._engine.begin() as conn:
            result = conn.execute(text("DELETE FROM users WHERE id = :id"), {"id": user_id})
            return result.rowcount > 0

    def list_tasks(
        self,
        status_id: Optional[int] = None,
        assignee_id: Optional[int] = None,
        due_date: Optional[date] = None,
        due_before: Optional[date] = None,
        limit: int = 200,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        where = []
        params: Dict[str, Any] = {"limit": limit, "offset": offset}

        if status_id is not None:
            where.append("t.status_id = :status_id")
            params["status_id"] = status_id
        if assignee_id is not None:
            where.append("t.assignee_id = :assignee_id")
            params["assignee_id"] = assignee_id
        if due_date is not None:
            where.append("t.due_date = :due_date")
            params["due_date"] = due_date
        if due_before is not None:
            where.append("t.due_date IS NOT NULL AND t.due_date <= :due_before")
            params["due_before"] = due_before

        where_sql = f"WHERE {' AND '.join(where)}" if where else ""

        sql = f"""
        SELECT
            t.id,
            t.title,
            t.description,
            t.status_id,
            s.name AS status,
            t.due_date,
            t.assignee_id,
            u.name AS assignee_name,
            t.created_at,
            t.updated_at
        FROM tasks t
        JOIN task_status s ON s.id = t.status_id
        LEFT JOIN users u ON u.id = t.assignee_id
        {where_sql}
        ORDER BY
            (t.due_date IS NULL) ASC,
            t.due_date ASC,
            t.id ASC
        LIMIT :limit OFFSET :offset
        """
        with self._engine.connect() as conn:
            rows = conn.execute(text(sql), params).mappings().all()
            return [dict(r) for r in rows]

    def get_task(self, task_id: int) -> Optional[Dict[str, Any]]:
        sql = """
        SELECT
            t.id,
            t.title,
            t.description,
            t.status_id,
            s.name AS status,
            t.due_date,
            t.assignee_id,
            u.name AS assignee_name,
            t.created_at,
            t.updated_at
        FROM tasks t
        JOIN task_status s ON s.id = t.status_id
        LEFT JOIN users u ON u.id = t.assignee_id
        WHERE t.id = :task_id
        """
        with self._engine.connect() as conn:
            row = conn.execute(text(sql), {"task_id": task_id}).mappings().first()
            return dict(row) if row else None

    def create_task(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        sql = """
        INSERT INTO tasks (title, description, status_id, due_date, assignee_id)
        VALUES (:title, :description, :status_id, :due_date, :assignee_id)
        RETURNING id
        """
        with self._engine.begin() as conn:
            new_id = conn.execute(text(sql), payload).scalar_one()
        task = self.get_task(int(new_id))
        if not task:
            raise RuntimeError("Task created but could not be reloaded")
        return task

    def update_task(self, task_id: int, patch: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if not patch:
            return self.get_task(task_id)

        allowed = {"title", "description", "status_id", "due_date", "assignee_id"}
        set_parts = []
        params: Dict[str, Any] = {"task_id": task_id}

        for k, v in patch.items():
            if k not in allowed:
                continue
            set_parts.append(f"{k} = :{k}")
            params[k] = v

        if not set_parts:
            return self.get_task(task_id)

        sql = f"UPDATE tasks SET {', '.join(set_parts)} WHERE id = :task_id"
        with self._engine.begin() as conn:
            result = conn.execute(text(sql), params)
            if result.rowcount == 0:
                return None

        return self.get_task(task_id)

    def delete_task(self, task_id: int) -> bool:
        with self._engine.begin() as conn:
            result = conn.execute(text("DELETE FROM tasks WHERE id = :task_id"), {"task_id": task_id})
            return result.rowcount > 0

    def dashboard_summary(self, upcoming_limit: int = 5) -> Dict[str, Any]:
        with self._engine.connect() as conn:
            total = conn.execute(text("SELECT COUNT(*) FROM tasks")).scalar_one()

            by_status = conn.execute(
                text(
                    """
                    SELECT s.id AS status_id, s.name AS status, COUNT(t.id) AS count
                    FROM task_status s
                    LEFT JOIN tasks t ON t.status_id = s.id
                    GROUP BY s.id, s.name
                    ORDER BY s.id
                    """
                )
            ).mappings().all()

            upcoming = conn.execute(
                text(
                    """
                    SELECT
                        t.id,
                        t.title,
                        t.description,
                        t.status_id,
                        s.name AS status,
                        t.due_date,
                        t.assignee_id,
                        u.name AS assignee_name,
                        t.created_at,
                        t.updated_at
                    FROM tasks t
                    JOIN task_status s ON s.id = t.status_id
                    LEFT JOIN users u ON u.id = t.assignee_id
                    WHERE t.due_date IS NOT NULL
                    ORDER BY t.due_date ASC, t.id ASC
                    LIMIT :limit
                    """
                ),
                {"limit": upcoming_limit},
            ).mappings().all()

        return {
            "total_tasks": int(total),
            "by_status": [dict(r) for r in by_status],
            "upcoming_deadlines": [dict(r) for r in upcoming],
        }
