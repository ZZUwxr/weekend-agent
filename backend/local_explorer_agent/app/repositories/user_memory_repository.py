from __future__ import annotations

import json
import os
import re
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from local_explorer_agent.app.domain.memory import (
    UserMemory,
    UserMemoryCompanion,
    UserMemoryContext,
    memory_to_context,
    new_default_memory,
)

_SAFE_USER_ID_RE = re.compile(r"[^A-Za-z0-9_.-]+")
_MAX_FEEDBACK_HISTORY = 50


class UserMemoryRepository:
    def __init__(self, data_dir: Path) -> None:
        self.data_dir = data_dir
        self.memory_dir = data_dir / "user_memory"

    def get_or_create(self, user_id: str) -> UserMemory:
        path = self._path_for(user_id)
        if not path.exists():
            memory = new_default_memory(
                self._safe_user_id(user_id),
                now=datetime.now(ZoneInfo("Asia/Shanghai")),
            )
            self.save(memory)
            return memory

        raw = json.loads(path.read_text(encoding="utf-8"))
        memory = UserMemory.model_validate(raw)
        if len(memory.feedback_history) > _MAX_FEEDBACK_HISTORY:
            memory.feedback_history = memory.feedback_history[-_MAX_FEEDBACK_HISTORY:]
            self.save(memory)
        return memory

    def get_context(self, user_id: str) -> UserMemoryContext:
        return memory_to_context(self.get_or_create(user_id))

    def get_context_for_companions(
        self,
        user_id: str,
        companion_ids: list[str] | None,
    ) -> UserMemoryContext:
        context = self.get_context(user_id)
        selected = _dedupe_ids(companion_ids or [])
        if not selected:
            return context
        filtered = [
            companion
            for companion in context.companions
            if companion.companion_id in selected
        ]
        return context.model_copy(update={
            "companions": filtered,
            "selected_companion_ids": [cid for cid in selected if any(c.companion_id == cid for c in filtered)],
        })

    def list_companions(self, user_id: str) -> list[UserMemoryCompanion]:
        memory = self.get_or_create(user_id)
        if not memory.companions:
            memory.companions = _default_companions()
            self.save(memory)
        return memory.companions

    def upsert_companion(
        self,
        user_id: str,
        companion: UserMemoryCompanion,
    ) -> UserMemoryCompanion:
        memory = self.get_or_create(user_id)
        if not memory.companions:
            memory.companions = _default_companions()
        companion.companion_id = _safe_companion_id(companion.companion_id)
        replaced = False
        for index, existing in enumerate(memory.companions):
            if existing.companion_id == companion.companion_id:
                memory.companions[index] = companion
                replaced = True
                break
        if not replaced:
            memory.companions.append(companion)
        memory.updated_at = datetime.now(ZoneInfo("Asia/Shanghai")).isoformat()
        self.save(memory)
        return companion

    def delete_companion(self, user_id: str, companion_id: str) -> bool:
        memory = self.get_or_create(user_id)
        safe_id = _safe_companion_id(companion_id)
        before = len(memory.companions)
        memory.companions = [
            companion for companion in memory.companions
            if companion.companion_id != safe_id
        ]
        changed = len(memory.companions) != before
        if changed:
            memory.updated_at = datetime.now(ZoneInfo("Asia/Shanghai")).isoformat()
            self.save(memory)
        return changed

    def save(self, memory: UserMemory) -> None:
        memory.user_id = self._safe_user_id(memory.user_id)
        memory.feedback_history = memory.feedback_history[-_MAX_FEEDBACK_HISTORY:]
        memory.preferences.category_weights = dict(memory.preferences.category_weights)
        memory.preferences.tag_weights = dict(memory.preferences.tag_weights)
        path = self._path_for(memory.user_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(
            memory.model_dump(),
            ensure_ascii=False,
            indent=2,
            default=str,
        )
        tmp_path = path.with_suffix(".tmp")
        tmp_path.write_text(payload, encoding="utf-8")
        os.replace(tmp_path, path)

    def _path_for(self, user_id: str) -> Path:
        safe_id = self._safe_user_id(user_id)
        path = (self.memory_dir / f"{safe_id}.json").resolve()
        memory_root = self.memory_dir.resolve()
        if memory_root not in path.parents:
            raise ValueError("Invalid user_id for memory path")
        return path

    def _safe_user_id(self, user_id: str) -> str:
        text = str(user_id or "").strip()
        if not text or "/" in text or "\\" in text or ".." in text:
            raise ValueError("Invalid user_id for memory path")
        safe = _SAFE_USER_ID_RE.sub("_", text)
        if not safe or safe in {".", ".."}:
            raise ValueError("Invalid user_id for memory path")
        return safe


def _safe_companion_id(companion_id: str) -> str:
    text = str(companion_id or "").strip()
    if not text or "/" in text or "\\" in text or ".." in text:
        raise ValueError("Invalid companion_id for memory")
    safe = _SAFE_USER_ID_RE.sub("_", text)
    if not safe or safe in {".", ".."}:
        raise ValueError("Invalid companion_id for memory")
    return safe[:80]


def _dedupe_ids(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        text = str(value or "").strip()
        if not text or text in seen:
            continue
        seen.add(text)
        result.append(text)
    return result


def _default_companions() -> list[UserMemoryCompanion]:
    return new_default_memory(
        "default_companion_seed",
        now=datetime.now(ZoneInfo("Asia/Shanghai")),
    ).companions
