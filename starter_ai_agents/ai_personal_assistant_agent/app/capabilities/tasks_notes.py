"""Tasks and notes capability - always enabled."""

from __future__ import annotations

from langchain_core.tools import tool

from app.capabilities import register_capability


def _get_tools(store, **kwargs):
    @tool
    def add_task(title: str, due_date: str = "") -> str:
        """Create a task. due_date must be in YYYY-MM-DD format when provided."""
        return store.add_task(title=title, due_date=due_date)

    @tool
    def list_tasks(include_completed: bool = False) -> str:
        """List tasks from personal memory."""
        return store.list_tasks(include_completed=include_completed)

    @tool
    def complete_task(task_id: str) -> str:
        """Mark a task complete using task id."""
        return store.complete_task(task_id=task_id)

    @tool
    def add_note(title: str, content: str) -> str:
        """Store a note with title and content."""
        return store.add_note(title=title, content=content)

    @tool
    def list_notes() -> str:
        """List all saved notes."""
        return store.list_notes()

    @tool
    def today_plan() -> str:
        """Show pending tasks due today."""
        return store.today_plan()

    return [add_task, list_tasks, complete_task, add_note, list_notes, today_plan]


register_capability("tasks_notes", _get_tools, enable_env_var=None)  # Always on
