#!/usr/bin/env python3
"""Merge supplement POI data into all_route_packs.json."""

import json
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
MAIN_FILE = SCRIPT_DIR / "generated_route_packs_30calls" / "all_route_packs.json"
SUPPLEMENT_DIR = SCRIPT_DIR / "generated_route_packs_30calls" / "supplement" / "json"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def merge() -> None:
    if not MAIN_FILE.exists():
        print(f"[ERROR] 主数据文件不存在：{MAIN_FILE}")
        return

    if not SUPPLEMENT_DIR.exists():
        print(f"[ERROR] 补充数据目录不存在：{SUPPLEMENT_DIR}")
        return

    main_data = load_json(MAIN_FILE)
    supplement_files = sorted(SUPPLEMENT_DIR.glob("*.json"))
    supplement_files = [f for f in supplement_files if "_failed_attempt_" not in f.name]

    if not supplement_files:
        print("[WARN] 没有找到补充数据文件")
        return

    print(f"[INFO] 主数据：{len(main_data.get('pois', []))} 个 POI")
    print(f"[INFO] 补充文件：{len(supplement_files)} 个")

    existing_poi_names = {str(p.get("name")) for p in main_data.get("pois", []) if isinstance(p, dict)}

    new_tasks = []
    new_plans = []
    new_pois = []
    new_edges = []
    new_feedback = []
    skipped = 0

    for path in supplement_files:
        data = load_json(path)
        plan = data.get("plan", {})

        # Check for duplicate POI names
        plan_pois = plan.get("pois", [])
        has_dup = any(str(p.get("name")) in existing_poi_names for p in plan_pois if isinstance(p, dict))
        if has_dup:
            print(f"[SKIP] {path.name}：POI name 与现有数据重复")
            skipped += 1
            continue

        new_tasks.append(data)
        new_plans.append({
            "task_id": data.get("task_id"),
            "scene_id": data.get("scene_id"),
            "scene_name": data.get("scene_name"),
            "route_index": data.get("route_index"),
            "route_style": data.get("route_style"),
            **plan,
        })

        for poi in plan_pois:
            if isinstance(poi, dict):
                new_pois.append({
                    "task_id": data.get("task_id"),
                    "scene_id": data.get("scene_id"),
                    "plan_id": plan.get("plan_id"),
                    **poi,
                })
                existing_poi_names.add(str(poi.get("name")))

        for edge in plan.get("route_edges", []):
            if isinstance(edge, dict):
                new_edges.append({
                    "task_id": data.get("task_id"),
                    "scene_id": data.get("scene_id"),
                    "plan_id": plan.get("plan_id"),
                    **edge,
                })

        for feedback in plan.get("sample_feedback", []):
            if isinstance(feedback, dict):
                new_feedback.append({
                    "task_id": data.get("task_id"),
                    "scene_id": data.get("scene_id"),
                    "plan_id": plan.get("plan_id"),
                    **feedback,
                })

    if not new_tasks:
        print("[WARN] 没有可合并的补充数据（全部被跳过）")
        return

    # Merge
    main_data.setdefault("tasks", [])
    main_data.setdefault("plans", [])
    main_data.setdefault("pois", [])
    main_data.setdefault("route_edges", [])
    main_data.setdefault("sample_feedback", [])

    main_data["tasks"].extend(new_tasks)
    main_data["plans"].extend(new_plans)
    main_data["pois"].extend(new_pois)
    main_data["route_edges"].extend(new_edges)
    main_data["sample_feedback"].extend(new_feedback)

    # Update summary
    main_data["summary"] = {
        "task_count": len(main_data["tasks"]),
        "plan_count": len(main_data["plans"]),
        "poi_count": len(main_data["pois"]),
        "route_edge_count": len(main_data["route_edges"]),
        "sample_feedback_count": len(main_data["sample_feedback"]),
    }

    write_json(MAIN_FILE, main_data)

    print(f"\n[OK] 合并完成")
    print(f"  新增任务：{len(new_tasks)}")
    print(f"  新增 POI：{len(new_pois)}")
    print(f"  跳过：{skipped}")
    print(f"  总计 POI：{main_data['summary']['poi_count']}")


if __name__ == "__main__":
    merge()
