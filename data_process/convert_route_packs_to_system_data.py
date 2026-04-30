#!/usr/bin/env python3
"""Convert generated route packs into backend data files.

The backend repositories prefer non-sample files when present:
`poi.json`, `route_edges.json`, and `queue_status.json`.
By default this converter writes only generated POIs/routes into the active
backend data files. Use `--merge-sample` only when you explicitly want to keep
the original sample data mixed in. Generated POI IDs are route-scoped so
duplicated names like `POI_1` do not collide.
"""

from __future__ import annotations

import argparse
import json
import re
from copy import deepcopy
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "data_process/generated_route_packs_30calls/all_route_packs.json"
DEFAULT_DATA_DIR = ROOT / "local_explorer_agent/app/data"
DEFAULT_ARCHIVE_DIR = ROOT / "data_process/generated_route_packs_30calls/system_converted"

SCORE_FIELDS = ("photo_score", "conversation_score", "novelty_score", "relax_score")
RISK_TO_QUEUE_MINUTES = {"low": 8, "medium": 18, "high": 42}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    parser.add_argument("--archive-dir", type=Path, default=DEFAULT_ARCHIVE_DIR)
    parser.add_argument(
        "--merge-sample",
        action="store_true",
        help="Merge existing sample data into system files. Default is generated data only.",
    )
    args = parser.parse_args()

    source = load_json(args.input)
    id_map = build_id_map(source.get("pois", []))
    generated_pois = [normalize_poi(item, id_map) for item in source.get("pois", [])]
    generated_routes = [
        normalize_route_edge(item, id_map) for item in source.get("route_edges", [])
    ]
    generated_queue = [queue_status_for_poi(item) for item in generated_pois]
    converted_plans = [normalize_plan(item, id_map) for item in source.get("plans", [])]
    converted_feedback = [
        normalize_feedback(item, id_map) for item in source.get("sample_feedback", [])
    ]

    sample_pois = load_json(args.data_dir / "poi.sample.json") if args.merge_sample else []
    sample_routes = load_json(args.data_dir / "route_edges.sample.json") if args.merge_sample else []
    sample_queue = load_json(args.data_dir / "queue_status.sample.json") if args.merge_sample else []

    poi_payload = dedupe_by_key([*sample_pois, *generated_pois], "id")
    route_payload = dedupe_routes([*sample_routes, *generated_routes])
    queue_payload = dedupe_by_key([*sample_queue, *generated_queue], "poi_id")

    args.data_dir.mkdir(parents=True, exist_ok=True)
    write_json(args.data_dir / "poi.json", poi_payload)
    write_json(args.data_dir / "route_edges.json", route_payload)
    write_json(args.data_dir / "queue_status.json", queue_payload)

    args.archive_dir.mkdir(parents=True, exist_ok=True)
    write_json(args.archive_dir / "poi.json", generated_pois)
    write_json(args.archive_dir / "route_edges.json", generated_routes)
    write_json(args.archive_dir / "queue_status.json", generated_queue)
    write_json(args.archive_dir / "route_pack_plans.json", converted_plans)
    write_json(args.archive_dir / "sample_feedback.json", converted_feedback)

    report = {
        "input": str(args.input),
        "system_outputs": {
            "poi": str(args.data_dir / "poi.json"),
            "route_edges": str(args.data_dir / "route_edges.json"),
            "queue_status": str(args.data_dir / "queue_status.json"),
        },
        "archive_dir": str(args.archive_dir),
        "source_summary": source.get("summary", {}),
        "generated_counts": {
            "poi": len(generated_pois),
            "route_edges": len(generated_routes),
            "queue_status": len(generated_queue),
            "route_pack_plans": len(converted_plans),
            "sample_feedback": len(converted_feedback),
        },
        "system_counts": {
            "poi": len(poi_payload),
            "route_edges": len(route_payload),
            "queue_status": len(queue_payload),
        },
        "id_prefix": "gen_{task_id}_{original_poi_id}",
        "merged_sample_data": args.merge_sample,
    }
    write_json(args.archive_dir / "conversion_report.json", report)
    print(json.dumps(report, ensure_ascii=False, indent=2))


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def build_id_map(pois: list[dict[str, Any]]) -> dict[tuple[str, str], str]:
    mapping: dict[tuple[str, str], str] = {}
    used: set[str] = set()
    for poi in pois:
        task_id = str(poi["task_id"])
        old_id = str(poi["id"])
        base = f"gen_{slug(task_id)}_{slug(old_id)}"
        new_id = base
        suffix = 2
        while new_id in used:
            new_id = f"{base}_{suffix}"
            suffix += 1
        mapping[(task_id, old_id)] = new_id
        used.add(new_id)
    return mapping


def normalize_poi(
    item: dict[str, Any],
    id_map: dict[tuple[str, str], str],
    *,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    poi = deepcopy(item)
    context = context or {}
    task_id = str(poi.get("task_id") or context["task_id"])
    old_id = str(poi["id"])
    route_tags = listify(poi.pop("route_tags", []))
    poi["id"] = id_map[(task_id, old_id)]
    poi["task_id"] = task_id
    poi.setdefault("scene_id", context.get("scene_id"))
    poi.setdefault("plan_id", context.get("plan_id"))
    poi.pop("task_id", None)
    poi.pop("scene_id", None)
    poi.pop("plan_id", None)
    poi["experience_scores"] = {
        key: clamp_score(poi.pop(key, 0)) for key in SCORE_FIELDS
    }
    poi["avg_price"] = as_int_or_none(poi.get("avg_price"))
    poi["avg_stay_minutes"] = as_int_or_none(poi.get("avg_stay_minutes"))
    poi["energy_level"] = int(clamp_number(poi.get("energy_level", 1), 0, 5))
    poi["indoor"] = bool(poi.get("indoor", True))
    poi["weather_fit"] = listify(poi.get("weather_fit"))
    poi["suitable_for"] = listify(poi.get("suitable_for"))
    poi["activity_tags"] = listify(poi.get("activity_tags"))
    poi["mood_tags"] = listify(poi.get("mood_tags"))
    poi["conflict_relief_tags"] = unique_strings(
        [
            *listify(poi.get("conflict_relief_tags")),
            *route_tags,
        ]
    )
    poi.setdefault("facilities", {})
    poi.setdefault("business_rules", {})
    poi.setdefault("persona_fit", {})
    if "reservation_required" in poi:
        poi["business_rules"].setdefault("reservation_required", poi["reservation_required"])
    return poi


def normalize_route_edge(
    item: dict[str, Any],
    id_map: dict[tuple[str, str], str],
    *,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    edge = deepcopy(item)
    context = context or {}
    task_id = str(edge.get("task_id") or context["task_id"])
    edge["task_id"] = task_id
    edge.setdefault("scene_id", context.get("scene_id"))
    edge.setdefault("plan_id", context.get("plan_id"))
    edge["from"] = id_map[(task_id, str(edge["from"]))]
    edge["to"] = id_map[(task_id, str(edge["to"]))]
    edge.pop("task_id", None)
    edge.pop("scene_id", None)
    edge.pop("plan_id", None)
    edge["distance_meters"] = int(edge.get("distance_meters") or 0)
    edge["walking_minutes"] = int(edge.get("walking_minutes") or 0)
    edge["cycling_minutes"] = as_int_or_none(edge.get("cycling_minutes"))
    edge["taxi_minutes"] = as_int_or_none(edge.get("taxi_minutes"))
    edge["subway_minutes"] = as_int_or_none(edge.get("subway_minutes"))
    edge["subway_transfer_count"] = int(edge.get("subway_transfer_count") or 0)
    edge["transit_modes"] = listify(edge.get("transit_modes"))
    edge["suitable_weather"] = listify(edge.get("suitable_weather"))
    edge["energy_cost"] = int(clamp_number(edge.get("energy_cost", 1), 0, 5))
    return edge


def queue_status_for_poi(poi: dict[str, Any]) -> dict[str, Any]:
    risk = str(poi.get("queue_risk") or "medium")
    return {
        "poi_id": poi["id"],
        "queue_minutes": RISK_TO_QUEUE_MINUTES.get(risk, 18),
        "risk": risk if risk in RISK_TO_QUEUE_MINUTES else "medium",
        "mock_scenario": "generated_route_pack",
    }


def normalize_plan(item: dict[str, Any], id_map: dict[tuple[str, str], str]) -> dict[str, Any]:
    plan = deepcopy(item)
    task_id = str(plan["task_id"])
    context = {
        "task_id": task_id,
        "scene_id": plan.get("scene_id"),
        "plan_id": plan.get("plan_id"),
    }
    plan["pois"] = [normalize_poi(poi, id_map, context=context) for poi in plan.get("pois", [])]
    plan["route_edges"] = [
        normalize_route_edge(edge, id_map, context=context) for edge in plan.get("route_edges", [])
    ]
    return plan


def normalize_feedback(item: dict[str, Any], id_map: dict[tuple[str, str], str]) -> dict[str, Any]:
    feedback = deepcopy(item)
    task_id = str(feedback["task_id"])
    for update in feedback.get("poi_updates", []):
        old_id = str(update.get("poi_id"))
        if (task_id, old_id) in id_map:
            update["source_poi_id"] = old_id
            update["poi_id"] = id_map[(task_id, old_id)]
    return feedback


def dedupe_by_key(items: list[dict[str, Any]], key: str) -> list[dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for item in items:
        result[str(item[key])] = item
    return list(result.values())


def dedupe_routes(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result: dict[tuple[str, str], dict[str, Any]] = {}
    for item in items:
        result[(str(item["from"]), str(item["to"]))] = item
    return list(result.values())


def slug(value: str) -> str:
    cleaned = re.sub(r"[^0-9A-Za-z_]+", "_", value.strip())
    cleaned = re.sub(r"_+", "_", cleaned).strip("_").lower()
    return cleaned or "unknown"


def listify(value: Any) -> list[str]:
    if value is None:
        return []
    values = value if isinstance(value, list) else [value]
    return unique_strings(str(item).strip() for item in values if str(item).strip())


def unique_strings(values: Any) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if not value or value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


def clamp_score(value: Any) -> float:
    return round(clamp_number(value, 0, 5), 2)


def clamp_number(value: Any, low: float, high: float) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        number = low
    return max(low, min(high, number))


def as_int_or_none(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(round(float(value)))
    except (TypeError, ValueError):
        return None


if __name__ == "__main__":
    main()
