import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class JSONRepository:
    def __init__(self, data_dir: Path) -> None:
        self.data_dir = data_dir

    def load_json(self, filename: str, default: Any | None = None) -> Any:
        path = self.resolve_json_path(filename)
        if not path.exists():
            logger.warning("JSON data file is missing: %s", path)
            return [] if default is None else default
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            logger.exception("JSON data file is invalid: %s", path)
            return [] if default is None else default

    def resolve_json_path(self, filename: str) -> Path:
        for candidate in self._candidate_filenames(filename):
            path = self.data_dir / candidate
            if path.exists():
                return path
        return self.data_dir / self._candidate_filenames(filename)[0]

    def _candidate_filenames(self, filename: str) -> list[str]:
        if ".sample." in filename:
            return [filename.replace(".sample", ""), filename]
        if filename.endswith(".json"):
            sample_name = filename.replace(".json", ".sample.json")
            return [filename, sample_name]
        return [filename]

    def save_json(self, filename: str, payload: Any) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        path = self.data_dir / filename
        path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
