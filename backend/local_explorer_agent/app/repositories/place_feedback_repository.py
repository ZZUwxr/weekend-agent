from __future__ import annotations

import json
import os
import re
from pathlib import Path

from local_explorer_agent.app.domain.place_feedback import (
    PlaceFeedbackFile,
    PlaceFeedbackRecord,
    PlaceFeedbackSummary,
    summarize_place_feedback,
)

_SAFE_ID_RE = re.compile(r"[^A-Za-z0-9_.-]+")
_MAX_RECORDS_PER_PLACE = 200


class PlaceFeedbackRepository:
    def __init__(self, data_dir: Path) -> None:
        self.data_dir = data_dir
        self.feedback_dir = data_dir / "place_feedback"

    def add_feedback(self, record: PlaceFeedbackRecord) -> PlaceFeedbackSummary:
        data = self._load_file(record.poi_id)
        data.records.append(record)
        data.records = data.records[-_MAX_RECORDS_PER_PLACE:]
        self._save_file(data)
        return summarize_place_feedback(data.poi_id, data.records)

    def get_summary(self, poi_id: str) -> PlaceFeedbackSummary:
        data = self._load_file(poi_id)
        return summarize_place_feedback(data.poi_id, data.records)

    def get_summaries(self, poi_ids: list[str]) -> dict[str, PlaceFeedbackSummary]:
        summaries: dict[str, PlaceFeedbackSummary] = {}
        for poi_id in poi_ids:
            summary = self.get_summary(poi_id)
            if summary.feedback_count > 0:
                summaries[poi_id] = summary
        return summaries

    def _load_file(self, poi_id: str) -> PlaceFeedbackFile:
        safe_id = self._safe_id(poi_id)
        path = self._path_for(safe_id)
        if not path.exists():
            return PlaceFeedbackFile(poi_id=safe_id)
        return PlaceFeedbackFile.model_validate(json.loads(path.read_text(encoding="utf-8")))

    def _save_file(self, data: PlaceFeedbackFile) -> None:
        data.poi_id = self._safe_id(data.poi_id)
        data.records = data.records[-_MAX_RECORDS_PER_PLACE:]
        path = self._path_for(data.poi_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(
            data.model_dump(),
            ensure_ascii=False,
            indent=2,
            default=str,
        )
        tmp_path = path.with_suffix(".tmp")
        tmp_path.write_text(payload, encoding="utf-8")
        os.replace(tmp_path, path)

    def _path_for(self, poi_id: str) -> Path:
        safe_id = self._safe_id(poi_id)
        path = (self.feedback_dir / f"{safe_id}.json").resolve()
        feedback_root = self.feedback_dir.resolve()
        if feedback_root not in path.parents:
            raise ValueError("Invalid poi_id for place feedback path")
        return path

    def _safe_id(self, value: str) -> str:
        text = str(value or "").strip()
        if not text or "/" in text or "\\" in text or ".." in text:
            raise ValueError("Invalid poi_id for place feedback path")
        safe = _SAFE_ID_RE.sub("_", text)
        if not safe or safe in {".", ".."}:
            raise ValueError("Invalid poi_id for place feedback path")
        return safe
