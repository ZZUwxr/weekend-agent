import json
import os
import re
from pathlib import Path

from local_explorer_agent.app.agent.react.state import AgentState
from local_explorer_agent.app.core.exceptions import NotFoundError
from local_explorer_agent.app.domain.models import PlanOutput

_SAFE_SESSION_RE = re.compile(r"[^A-Za-z0-9_.-]+")


class SessionStore:
    def __init__(self, data_dir: Path | None = None) -> None:
        self._plans: dict[str, PlanOutput] = {}
        self._agent_states: dict[str, AgentState] = {}
        self.runtime_dir = data_dir / "runtime" / "sessions" if data_dir else None

    def save(self, plan: PlanOutput) -> PlanOutput:
        self._plans[plan.session_id] = plan
        self._persist_model("plans", plan.session_id, plan)
        return plan

    def get(self, session_id: str) -> PlanOutput:
        if session_id in self._plans:
            return self._plans[session_id]
        loaded = self._load_model("plans", session_id, PlanOutput)
        if loaded is None:
            raise NotFoundError(f"Plan session {session_id} not found")
        self._plans[session_id] = loaded
        return loaded

    def update(self, plan: PlanOutput) -> PlanOutput:
        self._plans[plan.session_id] = plan
        self._persist_model("plans", plan.session_id, plan)
        return plan

    def save_agent_state(self, session_id: str, state: AgentState) -> None:
        self._agent_states[session_id] = state
        self._persist_model("agent_states", session_id, state)

    def get_agent_state(self, session_id: str) -> AgentState:
        if session_id in self._agent_states:
            return self._agent_states[session_id]
        loaded = self._load_model("agent_states", session_id, AgentState)
        if loaded is None:
            raise NotFoundError(f"Agent state for session {session_id} not found")
        self._agent_states[session_id] = loaded
        return loaded

    def _persist_model(self, bucket: str, item_id: str, model) -> None:
        if self.runtime_dir is None:
            return
        path = self._path_for(bucket, item_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(model.model_dump(mode="json"), ensure_ascii=False, indent=2)
        tmp_path = path.with_suffix(".tmp")
        tmp_path.write_text(payload, encoding="utf-8")
        os.replace(tmp_path, path)

    def _load_model(self, bucket: str, item_id: str, model_class):
        if self.runtime_dir is None:
            return None
        path = self._path_for(bucket, item_id)
        if not path.exists():
            return None
        return model_class.model_validate(json.loads(path.read_text(encoding="utf-8")))

    def _path_for(self, bucket: str, item_id: str) -> Path:
        assert self.runtime_dir is not None
        safe_id = _safe_id(item_id)
        path = (self.runtime_dir / bucket / f"{safe_id}.json").resolve()
        root = (self.runtime_dir / bucket).resolve()
        if root not in path.parents:
            raise ValueError("Invalid session path")
        return path


def _safe_id(item_id: str) -> str:
    text = str(item_id or "").strip()
    if not text or "/" in text or "\\" in text or ".." in text:
        raise ValueError("Invalid session id")
    safe = _SAFE_SESSION_RE.sub("_", text)
    if not safe or safe in {".", ".."}:
        raise ValueError("Invalid session id")
    return safe
