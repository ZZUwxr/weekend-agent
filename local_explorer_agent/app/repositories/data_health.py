import json
from pathlib import Path
from typing import Any

DATA_FILE_SPECS: dict[str, dict[str, object]] = {
    "poi": {
        "candidates": ["poi.json", "poi.sample.json"],
        "required_keys": ["id", "name", "category", "city", "lon", "lat"],
        "critical": True,
    },
    "route_edges": {
        "candidates": ["route_edges.json", "route_edges.sample.json"],
        "required_keys": ["from", "to", "distance_meters"],
        "critical": True,
    },
    "queue_status": {
        "candidates": ["queue_status.json", "queue_status.sample.json"],
        "required_keys": ["poi_id", "queue_minutes", "risk"],
        "critical": True,
    },
    "weather": {
        "candidates": ["weather.json", "weather.sample.json"],
        "required_keys": ["city", "condition"],
        "critical": False,
    },
    "user_profiles": {
        "candidates": ["user_profiles.json", "user_profiles.sample.json"],
        "required_keys": ["user_id"],
        "critical": False,
    },
    "booking_records": {
        "candidates": ["booking_records.json", "booking_records.sample.json"],
        "required_keys": [],
        "critical": False,
    },
}


def check_data_health(data_dir: Path) -> dict[str, Any]:
    files: dict[str, Any] = {}
    warnings: list[str] = []
    for logical_name, spec in DATA_FILE_SPECS.items():
        candidates = list(spec["candidates"])
        required_keys = list(spec["required_keys"])
        path = _first_existing(data_dir, candidates)
        file_health = {
            "logical_name": logical_name,
            "exists": path is not None,
            "path": str(path or data_dir / candidates[0]),
            "record_count": 0,
            "missing_required_fields": 0,
            "warnings": [],
        }
        if path is None:
            message = f"{logical_name} data file is missing"
            file_health["warnings"].append(message)
            warnings.append(message)
            files[logical_name] = file_health
            continue

        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            message = f"{logical_name} data file is invalid JSON: {exc.msg}"
            file_health["warnings"].append(message)
            warnings.append(message)
            files[logical_name] = file_health
            continue

        records = payload if isinstance(payload, list) else [payload]
        file_health["record_count"] = len(records)
        missing_count = _count_missing_required_fields(records, required_keys)
        file_health["missing_required_fields"] = missing_count
        if missing_count:
            message = f"{logical_name} has {missing_count} records missing required fields"
            file_health["warnings"].append(message)
            warnings.append(message)
        if not records and spec["critical"]:
            message = f"{logical_name} is critical but empty"
            file_health["warnings"].append(message)
            warnings.append(message)
        files[logical_name] = file_health

    critical_missing = [
        name
        for name, spec in DATA_FILE_SPECS.items()
        if spec["critical"] and not files[name]["exists"]
    ]
    overall_status = "ok" if not warnings else "warning"
    if critical_missing:
        overall_status = "degraded"
    return {
        "data_dir": str(data_dir),
        "overall_status": overall_status,
        "files": files,
        "warnings": warnings,
    }


def _first_existing(data_dir: Path, candidates: list[str]) -> Path | None:
    for candidate in candidates:
        path = data_dir / candidate
        if path.exists():
            return path
    return None


def _count_missing_required_fields(records: list[Any], required_keys: list[str]) -> int:
    if not required_keys:
        return 0
    return sum(
        1
        for record in records
        if not isinstance(record, dict) or any(key not in record for key in required_keys)
    )
