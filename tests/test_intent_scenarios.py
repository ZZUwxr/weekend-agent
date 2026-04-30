"""10 个意图明确的场景测试，验证最终方案是否满足用户核心诉求。"""
import json

import pytest

requests = pytest.importorskip("requests")

BASE = "http://127.0.0.1:8000/api/v1/plans/preview"

SCENARIOS = [
    {
        "id": 1,
        "label": "朋友烧烤",
        "query": "周末和朋友想去吃烧烤，找个氛围好的烧烤店",
        "expect_category": "烧烤",
        "expect_keywords": ["烧烤"],
    },
    {
        "id": 2,
        "label": "亲子游乐园",
        "query": "带孩子去游乐园玩，孩子6岁，喜欢刺激的项目",
        "expect_category": "游乐园",
        "expect_keywords": ["游乐园"],
    },
    {
        "id": 3,
        "label": "情侣火锅",
        "query": "和女朋友晚上想吃火锅，要辣的，环境好一点",
        "expect_category": "火锅",
        "expect_keywords": ["火锅"],
    },
    {
        "id": 4,
        "label": "独处看展览",
        "query": "一个人周末想去看个展览，文艺一点的",
        "expect_category": "展览",
        "expect_keywords": ["展览"],
    },
    {
        "id": 5,
        "label": "朋友桌游",
        "query": "三个朋友想玩桌游，找个桌游吧待一下午",
        "expect_category": "桌游",
        "expect_keywords": ["桌游"],
    },
    {
        "id": 6,
        "label": "亲子甜品",
        "query": "带女儿去吃甜品，她喜欢好看的蛋糕和冰淇淋",
        "expect_category": "甜品",
        "expect_keywords": ["甜品", "蛋糕", "冰淇淋"],
    },
    {
        "id": 7,
        "label": "独处书店",
        "query": "想找个安静的书店待一会儿，看看书喝杯茶",
        "expect_category": "书店",
        "expect_keywords": ["书店", "书局", "书舍"],
    },
    {
        "id": 8,
        "label": "朋友密室逃脱",
        "query": "四个朋友想去玩密室逃脱，要刺激的恐怖主题",
        "expect_category": "密室逃脱",
        "expect_keywords": ["密室"],
    },
    {
        "id": 9,
        "label": "家庭轻食",
        "query": "全家一起吃个轻食，老婆在健身要低卡的，孩子也能吃",
        "expect_category": "轻食",
        "expect_keywords": ["轻食"],
    },
    {
        "id": 10,
        "label": "亲子空间",
        "query": "带2岁宝宝去亲子空间玩，要安全的室内场所",
        "expect_category": "亲子空间",
        "expect_keywords": ["亲子", "儿童"],
    },
]


def run_scenario(sc):
    payload = {
        "user_id": f"test_{sc['id']:02d}",
        "query": sc["query"],
        "city": "深圳",
        "start_time": "2026-05-10T14:00:00",
        "duration_minutes": 180,
        "location": {"lat": 22.54, "lon": 114.05},
    }
    try:
        resp = requests.post(BASE, json=payload, timeout=120)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        return {"error": str(e)}


def analyze(sc, data):
    if "error" in data:
        return {
            "pass": False,
            "reason": f"请求失败: {data['error']}",
            "matched_pois": [],
            "all_stages": [],
        }

    recommended_id = data.get("recommended_plan_id")
    candidates = data.get("plan_candidates", [])
    recommended = next(
        (c for c in candidates if c.get("plan_id") == recommended_id),
        candidates[0] if candidates else {},
    )

    stages = recommended.get("stages", [])
    all_poi_names = []
    all_poi_categories = []
    stage_details = []
    for s in stages:
        poi = s.get("selected_poi") or {}
        name = poi.get("name", "")
        cat = poi.get("category", "")
        all_poi_names.append(name)
        all_poi_categories.append(cat)
        stage_details.append(
            f"{s.get('stage_type', '?')}→{name}({cat})"
        )

    # Check if any expected keyword appears in POI names or categories
    matched = []
    for kw in sc["expect_keywords"]:
        for name, cat in zip(all_poi_names, all_poi_categories, strict=False):
            if kw in name or kw in cat:
                matched.append(f"{name}({cat})")
                break

    passed = len(matched) > 0
    reason = ""
    if not passed:
        reason = (
            f"期望包含「{sc['expect_category']}」类POI，"
            f"但推荐方案所有阶段为: {stage_details}"
        )

    return {
        "pass": passed,
        "reason": reason,
        "matched_pois": matched,
        "all_stages": stage_details,
        "recommended_title": recommended.get("title", ""),
        "overall_score": recommended.get("overall_score"),
        "candidates_count": len(candidates),
        "session_id": data.get("session_id", ""),
    }


def main():
    results = []
    for sc in SCENARIOS:
        print(f"[{sc['id']:02d}/10] 测试中: {sc['label']} ...", flush=True)
        data = run_scenario(sc)
        result = analyze(sc, data)
        result["scenario"] = sc
        results.append(result)
        status = "PASS ✓" if result["pass"] else "FAIL ✗"
        print(f"       {status}  {result['all_stages']}", flush=True)

    # Summary
    print("\n" + "=" * 80)
    print("测试结果汇总")
    print("=" * 80)
    passed = sum(1 for r in results if r["pass"])
    failed = len(results) - passed
    print(f"通过: {passed}/10  失败: {failed}/10\n")

    for r in results:
        sc = r["scenario"]
        status = "PASS" if r["pass"] else "FAIL"
        print(f"[{status}] 场景{sc['id']}: {sc['label']}")
        print(f"    输入: {sc['query']}")
        print(
            f"    推荐: {r.get('recommended_title', 'N/A')} "
            f"(score={r.get('overall_score', 'N/A')})"
        )
        print(f"    方案: {r['all_stages']}")
        if r["matched_pois"]:
            print(f"    匹配: {r['matched_pois']}")
        if not r["pass"]:
            print(f"    原因: {r['reason']}")
        print()

    # Save JSON for report generation
    with open("/tmp/intent_test_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2, default=str)
    print("详细结果已保存到 /tmp/intent_test_results.json")


if __name__ == "__main__":
    main()
