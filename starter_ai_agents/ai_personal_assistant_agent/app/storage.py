from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any


@dataclass
class AssistantState:
    tasks: list[dict[str, Any]] = field(default_factory=list)
    notes: list[dict[str, Any]] = field(default_factory=list)


class StateStore:
    def __init__(self, file_path: str):
        self.path = Path(file_path)
        if not self.path.exists():
            self.save(AssistantState())

    def load(self) -> AssistantState:
        raw = json.loads(self.path.read_text(encoding="utf-8"))
        return AssistantState(tasks=raw.get("tasks", []), notes=raw.get("notes", []))

    def save(self, state: AssistantState) -> None:
        payload = {"tasks": state.tasks, "notes": state.notes}
        self.path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def add_task(self, title: str, due_date: str = "") -> str:
        state = self.load()
        task_id = str(len(state.tasks) + 1)
        state.tasks.append(
            {
                "id": task_id,
                "title": title.strip(),
                "due_date": due_date.strip(),
                "completed": False,
            }
        )
        self.save(state)
        return f"Task created with id={task_id}."

    def list_tasks(self, include_completed: bool = False) -> str:
        state = self.load()
        tasks = state.tasks
        if not include_completed:
            tasks = [task for task in tasks if not task["completed"]]
        if not tasks:
            return "No tasks found."
        rows = []
        for task in tasks:
            status = "done" if task["completed"] else "todo"
            due = task["due_date"] or "-"
            rows.append(f"[{task['id']}] ({status}) {task['title']} | due: {due}")
        return "\n".join(rows)

    def complete_task(self, task_id: str) -> str:
        state = self.load()
        for task in state.tasks:
            if task["id"] == task_id:
                task["completed"] = True
                self.save(state)
                return f"Task {task_id} marked complete."
        return f"Task {task_id} not found."

    def add_note(self, title: str, content: str) -> str:
        state = self.load()
        state.notes.append({"title": title.strip(), "content": content.strip()})
        self.save(state)
        return "Note saved."

    def list_notes(self) -> str:
        state = self.load()
        if not state.notes:
            return "No notes found."
        lines = []
        for idx, note in enumerate(state.notes, start=1):
            lines.append(f"{idx}. {note['title']}: {note['content']}")
        return "\n".join(lines)

    def today_plan(self) -> str:
        today = date.today().isoformat()
        state = self.load()
        todays_tasks = [
            task
            for task in state.tasks
            if not task["completed"] and task.get("due_date", "").strip() == today
        ]
        if not todays_tasks:
            return f"No pending tasks due today ({today})."
        lines = [f"Tasks due today ({today}):"]
        for task in todays_tasks:
            lines.append(f"- [{task['id']}] {task['title']}")
        return "\n".join(lines)
