from __future__ import annotations

import json
import os
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from local_explorer_agent.app.domain.models import PlanCandidate, PlanOutput

_SAFE_ID_RE = re.compile(r"[^A-Za-z0-9_.-]+")
_MAX_HISTORY_ITEMS = 30
_DEFAULT_PLAN_ID = "plan-a"


class MobileStateRepository:
    """JSON-backed mobile app state keyed by anonymous device user id."""

    def __init__(self, data_dir: Path) -> None:
        self.root_dir = data_dir / "runtime" / "mobile_users"

    def get_state(self, user_id: str) -> dict[str, Any]:
        path = self._path_for(user_id)
        if not path.exists():
            return self._new_state(user_id)
        return _deep_merge(self._new_state(user_id), json.loads(path.read_text(encoding="utf-8")))

    def save_state(self, user_id: str, state: dict[str, Any]) -> dict[str, Any]:
        state["user_id"] = self._safe_id(user_id)
        path = self._path_for(user_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(state, ensure_ascii=False, indent=2, default=str)
        tmp_path = path.with_suffix(".tmp")
        tmp_path.write_text(payload, encoding="utf-8")
        os.replace(tmp_path, path)
        return state

    def get_active_travel(self, user_id: str) -> dict[str, Any] | None:
        active = self.get_state(user_id).get("active_travel")
        return active if isinstance(active, dict) and active.get("travel_id") else None

    def set_active_travel(
        self,
        user_id: str,
        *,
        travel_id: str,
        plan_id: str | None = None,
        state: str | None = None,
    ) -> dict[str, Any]:
        current = self.get_state(user_id)
        current["active_travel"] = {
            "travel_id": travel_id,
            "plan_id": _frontend_plan_id(plan_id),
            "state": state,
            "updated_at": _now_iso(),
        }
        return self.save_state(user_id, current)["active_travel"]

    def get_preference(self, user_id: str, key: str) -> dict[str, Any]:
        value = self.get_state(user_id).get("preferences", {}).get(key, {})
        return value if isinstance(value, dict) else {}

    def save_preference(self, user_id: str, key: str, payload: dict[str, Any]) -> str:
        state = self.get_state(user_id)
        state.setdefault("preferences", {})[key] = {
            **state.get("preferences", {}).get(key, {}),
            **payload,
            "updated_at": _now_iso(),
        }
        self.save_state(user_id, state)
        return state["preferences"][key]["updated_at"]

    def list_history(self, user_id: str) -> list[dict[str, Any]]:
        history = self.get_state(user_id).get("history", [])
        return history if isinstance(history, list) else []

    def record_plan(
        self,
        user_id: str,
        plan: PlanOutput,
        *,
        plan_id: str | None = None,
        status: str | None = None,
    ) -> None:
        state = self.get_state(user_id)
        frontend_plan_id = _frontend_plan_id(plan_id or plan.recommended_plan_id)
        state["active_travel"] = {
            "travel_id": plan.session_id,
            "plan_id": frontend_plan_id,
            "state": str(status or plan.state),
            "updated_at": _now_iso(),
        }
        item = _history_item_from_plan(plan, frontend_plan_id, status=status)
        history = [
            h for h in state.get("history", [])
            if h.get("travel_id") != plan.session_id
        ]
        state["history"] = [item, *history][:_MAX_HISTORY_ITEMS]
        self.save_state(user_id, state)

    def record_feedback(
        self,
        user_id: str,
        *,
        session_id: str,
        rating: int | None,
        tags: list[str],
        raw_feedback: str,
        feedback_id: str,
    ) -> None:
        state = self.get_state(user_id)
        for item in state.get("history", []):
            if item.get("travel_id") == session_id:
                item["rating"] = rating
                item["last_feedback"] = raw_feedback[:300]
                item["feedback_tags"] = tags[:12]
                item["feedback_id"] = feedback_id
                item["status"] = "feedback"
                item["updated_at"] = _now_iso()
                break
        self.save_state(user_id, state)

    def record_action(
        self,
        user_id: str,
        *,
        session_id: str,
        action_type: str,
        plan_id: str | None,
        payload: dict[str, Any],
        status: str = "pending_provider",
        code: str = "provider_unavailable",
        message: str = "外部服务暂未接入，已在后端记录为待处理任务。",
    ) -> dict[str, Any]:
        state = self.get_state(user_id)
        action = {
            "action_id": f"act_{uuid4().hex[:10]}",
            "session_id": session_id,
            "plan_id": _frontend_plan_id(plan_id),
            "action_type": action_type,
            "status": status,
            "code": code,
            "message": message,
            "payload": payload,
            "created_at": _now_iso(),
        }
        state.setdefault("actions", []).insert(0, action)
        state["actions"] = state["actions"][:100]
        self.save_state(user_id, state)
        return action

    def create_payment_order(
        self,
        user_id: str,
        *,
        session_id: str,
        plan_id: str | None,
        payment_method_id: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        action = self.record_action(
            user_id,
            session_id=session_id,
            plan_id=plan_id,
            action_type="payment_order",
            payload={**payload, "payment_method_id": payment_method_id},
            message="支付网关暂未接入，已生成后端待处理支付任务。",
        )
        action["order_id"] = f"order_{uuid4().hex[:12]}"
        state = self.get_state(user_id)
        for saved in state.get("actions", []):
            if saved.get("action_id") == action["action_id"]:
                saved.update({"order_id": action["order_id"]})
                break
        self.save_state(user_id, state)
        return action

    def _path_for(self, user_id: str) -> Path:
        safe_id = self._safe_id(user_id)
        path = (self.root_dir / f"{safe_id}.json").resolve()
        root = self.root_dir.resolve()
        if root not in path.parents:
            raise ValueError("Invalid mobile user path")
        return path

    def _safe_id(self, user_id: str) -> str:
        text = str(user_id or "").strip()
        if not text or "/" in text or "\\" in text or ".." in text:
            raise ValueError("Invalid mobile user id")
        safe = _SAFE_ID_RE.sub("_", text)
        if not safe or safe in {".", ".."}:
            raise ValueError("Invalid mobile user id")
        return safe

    def _new_state(self, user_id: str) -> dict[str, Any]:
        return {
            "user_id": self._safe_id(user_id),
            "active_travel": None,
            "preferences": {},
            "history": [],
            "actions": [],
            "created_at": _now_iso(),
        }


def _history_item_from_plan(
    plan: PlanOutput,
    plan_id: str,
    *,
    status: str | None,
) -> dict[str, Any]:
    candidate = _find_candidate(plan, plan_id)
    title = candidate.title if candidate else (plan.input_query[:24] or "周末出行")
    stages = candidate.stages if candidate else []
    route_summary = " → ".join(
        (stage.selected_poi.name if stage.selected_poi else stage.name)
        for stage in stages[:4]
    ) or plan.input_query[:36] or "已生成行程"
    total = sum(
        int(stage.selected_poi.avg_price or 0)
        for stage in stages
        if stage.selected_poi
    )
    created = plan.created_at if isinstance(plan.created_at, datetime) else datetime.now(UTC)
    return {
        "id": plan.session_id,
        "travel_id": plan.session_id,
        "plan_id": _frontend_plan_id(plan_id),
        "title": title,
        "date_line": created.astimezone().strftime("%m月%d日"),
        "meta_line": f"{created.astimezone().strftime('%m月%d日')} · {len(stages) or 1}站 · {'¥' + str(total) if total else '费用待确认'}",
        "route_summary": route_summary,
        "rating": None,
        "price_text": f"¥{total}" if total else "费用待确认",
        "status": str(status or plan.state),
        "updated_at": _now_iso(),
    }


def _find_candidate(plan: PlanOutput, plan_id: str | None) -> PlanCandidate | None:
    wanted = (plan_id or plan.recommended_plan_id or _DEFAULT_PLAN_ID).replace("-", "_")
    for candidate in plan.plan_candidates:
        if candidate.plan_id == wanted or candidate.plan_id.replace("_", "-") == plan_id:
            return candidate
    return plan.plan_candidates[0] if plan.plan_candidates else None


def _frontend_plan_id(plan_id: str | None) -> str:
    return (plan_id or _DEFAULT_PLAN_ID).replace("_", "-")


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    result = {**base}
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result
