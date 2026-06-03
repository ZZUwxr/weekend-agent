from __future__ import annotations

import json
import os
import re
from datetime import UTC, datetime
from pathlib import Path

from local_explorer_agent.app.domain.followup import FeedbackFollowupTask

_SAFE_ID_RE = re.compile(r"[^A-Za-z0-9_.-]+")


class FeedbackFollowupRepository:
    def __init__(self, data_dir: Path) -> None:
        self.data_dir = data_dir
        self.followup_dir = data_dir / "feedback_followups"

    def save(self, task: FeedbackFollowupTask) -> FeedbackFollowupTask:
        task.task_id = self._safe_id(task.task_id)
        path = self._path_for(task.task_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(
            task.model_dump(),
            ensure_ascii=False,
            indent=2,
            default=str,
        )
        tmp_path = path.with_suffix(".tmp")
        tmp_path.write_text(payload, encoding="utf-8")
        os.replace(tmp_path, path)
        return task

    def get(self, task_id: str) -> FeedbackFollowupTask:
        path = self._path_for(task_id)
        if not path.exists():
            raise KeyError(task_id)
        return FeedbackFollowupTask.model_validate(json.loads(path.read_text(encoding="utf-8")))

    def find_by_session(self, session_id: str) -> FeedbackFollowupTask | None:
        for task in self.list_all():
            if task.session_id == session_id:
                return task
        return None

    def list_due(
        self,
        *,
        user_id: str | None = None,
        now: datetime | None = None,
    ) -> list[FeedbackFollowupTask]:
        due_at = now or datetime.now(UTC)
        tasks: list[FeedbackFollowupTask] = []
        for task in self.list_all():
            if task.status not in {"scheduled", "sent"}:
                continue
            if user_id is not None and task.user_id != user_id:
                continue
            if _parse_datetime(task.due_at) <= due_at:
                tasks.append(task)
        return tasks

    def list_all(self) -> list[FeedbackFollowupTask]:
        if not self.followup_dir.exists():
            return []
        tasks: list[FeedbackFollowupTask] = []
        for path in sorted(self.followup_dir.glob("*.json")):
            tasks.append(
                FeedbackFollowupTask.model_validate(
                    json.loads(path.read_text(encoding="utf-8"))
                )
            )
        return tasks

    def _path_for(self, task_id: str) -> Path:
        safe_id = self._safe_id(task_id)
        path = (self.followup_dir / f"{safe_id}.json").resolve()
        followup_root = self.followup_dir.resolve()
        if followup_root not in path.parents:
            raise ValueError("Invalid task_id for followup path")
        return path

    def _safe_id(self, value: str) -> str:
        text = str(value or "").strip()
        if not text or "/" in text or "\\" in text or ".." in text:
            raise ValueError("Invalid task_id for followup path")
        safe = _SAFE_ID_RE.sub("_", text)
        if not safe or safe in {".", ".."}:
            raise ValueError("Invalid task_id for followup path")
        return safe


def _parse_datetime(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed
