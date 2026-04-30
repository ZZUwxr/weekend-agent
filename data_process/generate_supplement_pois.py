#!/usr/bin/env python3
"""Generate supplementary POI data for underrepresented categories.

Targets: 烧烤, 火锅, 游乐园, 密室逃脱, 亲子空间, 桌游, 烤肉

Uses the same LLM and schema as generated_data_byllm.py but reads from
route_designs_supplement.json instead of the main SCENES/ROUTE_BLUEPRINTS.
"""

import json
import os
import random
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
from dotenv import load_dotenv
from openai import OpenAI

try:
    from json_repair import repair_json
except Exception:
    repair_json = None


# ============================================================
# Config
# ============================================================

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent

load_dotenv(PROJECT_ROOT / ".env")
load_dotenv(SCRIPT_DIR / ".env", override=True)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
OPENAI_MODEL = os.getenv("OPENAI_MODEL")
SOURCE_POINTS_FILE = os.getenv("SOURCE_POINTS_FILE", "").strip()

USE_JSON_MODE = os.getenv("USE_JSON_MODE", "false").lower() == "true"
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "8000"))
CALL_DELAY_SECONDS = int(os.getenv("CALL_DELAY_SECONDS", "8"))
CANDIDATE_POINTS_PER_TASK = int(os.getenv("CANDIDATE_POINTS_PER_TASK", "14"))

if not OPENAI_API_KEY:
    raise RuntimeError("请在 .env 中设置 OPENAI_API_KEY")
if not OPENAI_MODEL:
    raise RuntimeError("请在 .env 中设置 OPENAI_MODEL")

client = OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)

OUTPUT_DIR = SCRIPT_DIR / "generated_route_packs_30calls" / "supplement"
JSON_DIR = OUTPUT_DIR / "json"
RAW_DIR = OUTPUT_DIR / "raw"
JSON_DIR.mkdir(parents=True, exist_ok=True)
RAW_DIR.mkdir(parents=True, exist_ok=True)

REGISTRY_FILE = SCRIPT_DIR / "generated_route_packs_30calls" / "used_registry.json"
SUPPLEMENT_DESIGNS_FILE = SCRIPT_DIR / "prompt" / "route_designs_supplement.json"

RANDOM_SEED = 42
MAX_RETRY_PER_TASK = 2

random.seed(RANDOM_SEED)


# ============================================================
# Load source points
# ============================================================

def load_source_points() -> List[Dict[str, Any]]:
    if not SOURCE_POINTS_FILE:
        raise RuntimeError("请在 .env 中设置 SOURCE_POINTS_FILE")
    path = Path(SOURCE_POINTS_FILE)
    if not path.exists():
        raise RuntimeError(f"SOURCE_POINTS_FILE 不存在：{path}")
    if path.suffix.lower() in [".xlsx", ".xls"]:
        df = pd.read_excel(path)
    elif path.suffix.lower() == ".csv":
        try:
            df = pd.read_csv(path, encoding="utf-8-sig")
        except UnicodeDecodeError:
            df = pd.read_csv(path, encoding="gbk")
    else:
        raise ValueError("SOURCE_POINTS_FILE 只支持 .xlsx / .xls / .csv")

    df.columns = [str(c).strip() for c in df.columns]
    required = {"Feature", "Instance", "Lon", "Lat"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"源点位文件缺少列：{missing}")

    df = df.dropna(subset=["Lon", "Lat"]).copy()
    points = []
    for _, row in df.iterrows():
        points.append({
            "source_feature": str(row["Feature"]).strip(),
            "source_instance": int(row["Instance"]),
            "lon": float(row["Lon"]),
            "lat": float(row["Lat"]),
        })
    print(f"[INFO] 已读取源点位 {len(points)} 个")
    return points


SOURCE_POINTS = load_source_points()


# ============================================================
# Registry
# ============================================================

def load_registry() -> Dict[str, Any]:
    if not REGISTRY_FILE.exists():
        return {"used_source_instances": [], "used_poi_names": [], "updated_at": None}
    return json.loads(REGISTRY_FILE.read_text(encoding="utf-8"))


def save_registry(registry: Dict[str, Any]) -> None:
    registry["updated_at"] = datetime.now().isoformat(timespec="seconds")
    REGISTRY_FILE.write_text(
        json.dumps(registry, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def update_registry_with_plan(plan_data: Dict[str, Any]) -> None:
    registry = load_registry()
    used_instances = set(int(x) for x in registry.get("used_source_instances", []))
    used_names = set(str(x) for x in registry.get("used_poi_names", []))
    for poi in plan_data.get("pois", []):
        if "source_instance" in poi:
            used_instances.add(int(poi["source_instance"]))
        if "name" in poi:
            used_names.add(str(poi["name"]))
    registry["used_source_instances"] = sorted(list(used_instances))
    registry["used_poi_names"] = sorted(list(used_names))
    save_registry(registry)


def sample_points_for_task(task_id: str, count: int) -> List[Dict[str, Any]]:
    registry = load_registry()
    used_instances = set(int(x) for x in registry.get("used_source_instances", []))
    available = [p for p in SOURCE_POINTS if int(p["source_instance"]) not in used_instances]
    if len(available) < count:
        raise RuntimeError(f"可用 source_points 不足。剩余 {len(available)}，需要 {count}")
    random.seed(f"{RANDOM_SEED}_{task_id}")
    return random.sample(available, count)


# ============================================================
# Prompt (reuse from main script)
# ============================================================

SYSTEM_PROMPT = """
你是一个高质量本地生活沙盒数据生成专家。

你正在为一个 Hackathon 项目生成 Local Activity Sandbox 数据。
项目主题是"周末闲时活动规划 Agent"。
目标是展示 Agent 的路线规划、动态重规划、用户画像和游后反馈闭环能力。

注意：
1. 你生成的是虚拟沙盒数据，不是真实商户数据。
2. 数据要具体、自洽、有决策冲突，不要所有地点都完美。
3. 输出必须是严格 JSON 对象，不要 Markdown，不要解释，不要使用 ```json 包裹。

【POI 命名要求 - 非常重要】
POI 名称必须是虚构的，但要像深圳本地真实会出现的店名、街区名或活动点名称。
不要直接使用真实知名品牌或真实商户全名；可以借鉴深圳商圈、城中村、街巷、写字楼、工业园和口语化小店的命名气质。

优先使用这些深圳语感锚点做组合，但不要每个名字都塞满地名：
- 蛇口、南油、后海、科技园、粤海、白石洲、华侨城、侨城东、车公庙、岗厦、皇岗村、梅林、八卦岭、西丽、宝安中心、海上世界、深圳湾、壹方城、福田中心、南头古城、侨香、上沙、下沙。
- 常见生活化后缀：茶档、糖水铺、小馆、饭堂、书局、咖啡、轻食、剧场、桌游吧、买手店、花房、露台、巷口、三楼、二楼、9号、B座、旧厂、社区店。

好的命名方向（多种风格混合使用）：
- 地名+品类：南油阿芬糖水、蛇口二号码头咖啡、白石洲三巷牛杂、车公庙边炉小馆。
- 人名/昵称+品类：阿娟甜品、老肖茶档、陈记饭堂、肥仔烧烤。
- 楼层/街巷/园区+品类：侨城东旧厂书局、梅林七号轻食、岗厦B座桌游吧、南头三楼小剧场。
- 中英混搭但自然：Tide Room海边茶室、LIME后海、OCT旧仓买手店、Nanyou Deli。
- 直白但不模板：楼下咖啡、巷口糖水、社区花房、二楼桌游吧。
- 更生活化的朋友局：南油肥仔烧烤、车公庙牛肉火锅、白石洲烤肉排档、岗厦桑拿鸡、梅林电竞馆、龙华真人CS、南山密室。

禁止的命名风格（一看就是 AI 生成的）：
- 禁止"悠然X"、"静心X"、"萌芽X"、"欢乐X"、"甜蜜X"、"星空X"、"时光X"、"阳光X"、"微风X"、"清心X"、"童趣X"、"奇幻X"、"绘梦X"、"乐享X"、"乐聚X"。
- 禁止"X小屋"、"X工坊"、"X空间"、"X天地"、"X驿站"这类模板化后缀。
- 禁止所有名字都是"形容词+名词+品类"的固定结构。
- 禁止名字像景区宣传语或儿童绘本标题。

每条路线的 4-5 个 POI 名字风格必须各不相同；至少 3 个名字要带有深圳地名、街巷楼层、人名昵称、数字、英文或口语化小店锚点之一。
"""

SCHEMA_REQUIREMENT = """
你必须严格返回以下 JSON 结构：

{
  "task_id": "string",
  "scene_id": "string",
  "scene_name": "string",
  "target_user": "string",
  "route_index": number,
  "route_style": "string",
  "plan": {
    "plan_id": "string",
    "title": "string",
    "route_style": "string",
    "summary": "string",
    "recommended_start_time": "string",
    "total_budget": number,
    "total_duration_minutes": number,
    "total_walking_minutes": number,
    "weather_fit": ["晴天", "雨天", "阴天", "高温"],
    "route_tags": ["string"],
    "suitable_for": ["string"],
    "risk_notes": ["string"],

    "pois": [
      {
        "id": "string",
        "source_instance": number,
        "source_feature": "string",
        "name": "string",
        "category": "咖啡|书店|甜品|轻食|茶馆|展览|手作体验|小剧场|桌游|公园|Citywalk|买手店|运动|亲子空间|游乐园|餐厅|烧烤|火锅|烤肉|桑拿鸡|电竞馆|网吧|密室逃脱|真人CS|KTV|洗浴汗蒸|夜间活动",
        "city": "深圳",
        "area": "科技生活区|海岸漫游区|艺术仓库区|商圈活力区|安静生活区",
        "lon": number,
        "lat": number,
        "address": "string",
        "avg_price": number,
        "open_hours": "string",
        "avg_stay_minutes": number,
        "reservation_required": boolean,
        "indoor": boolean,
        "weather_fit": ["string"],
        "energy_level": number,
        "crowd_risk": "low|medium|high",
        "queue_risk": "low|medium|high",
        "mood_tags": ["string"],
        "activity_tags": ["string"],
        "suitable_for": ["string"],
        "avoid_for": ["string"],
        "photo_score": number,
        "conversation_score": number,
        "novelty_score": number,
        "relax_score": number,
        "facilities": {
          "restroom": boolean,
          "pet_friendly": boolean,
          "charging_available": boolean,
          "wifi": boolean,
          "accessible": boolean,
          "baby_care_room": boolean,
          "luggage_storage": boolean,
          "air_conditioning": boolean,
          "seating_quality": "normal|good|excellent"
        },
        "transportation": {
          "subway": {
            "nearest_station": "string",
            "lines": ["string"],
            "exit": "string",
            "distance_meters": number,
            "walk_minutes": number,
            "recommended": boolean,
            "last_train_buffer_minutes": number,
            "access_note": "string"
          },
          "subway_station": "string",
          "subway_lines": ["string"],
          "subway_exit": "string",
          "subway_distance_meters": number,
          "subway_walk_minutes": number,
          "bus_distance_meters": number,
          "parking_available": boolean,
          "parking_fee": "string|null",
          "bike_parking_available": boolean,
          "taxi_dropoff_friendly": boolean,
          "walking_difficulty": "low|medium|high"
        },
        "business_rules": {
          "photo_allowed": boolean,
          "outside_food_allowed": boolean,
          "group_buy_available": boolean,
          "reservation_required": boolean,
          "takeaway_allowed": boolean,
          "refund_friendly": boolean,
          "min_spend": number,
          "time_limit_minutes": number|null,
          "age_restriction": string|null,
          "dress_code": string|null,
          "quiet_required": boolean,
          "pets_allowed_inside": boolean
        },
        "community_feedback": {
          "feedback_count": number,
          "positive_rate": number,
          "common_praises": ["string"],
          "common_issues": ["string"],
          "tag_votes": {"tag": number},
          "score_adjustments": {
            "photo_score": number,
            "conversation_score": number,
            "novelty_score": number,
            "relax_score": number
          }
        },
        "description": "string"
      }
    ],

    "route_edges": [
      {
        "from": "string",
        "to": "string",
        "distance_meters": number,
        "walking_minutes": number,
        "cycling_minutes": number,
        "taxi_minutes": number,
        "subway_recommended": boolean,
        "subway_minutes": number|null,
        "subway_transfer_count": number,
        "transit_modes": ["walking", "cycling", "taxi", "subway"],
        "route_type": "步行友好|普通街道|适合骑行|打车更优|室内连通|地铁更优",
        "scenic_score": number,
        "shade_score": number,
        "crowd_level": "low|medium|high",
        "suitable_weather": ["string"],
        "energy_cost": number,
        "route_note": "string"
      }
    ],

    "backup_plans": [
      {
        "trigger": "string",
        "action": "string",
        "replace_poi_id": "string|null",
        "suggested_poi": "string",
        "reason": "string"
      }
    ],

    "sample_feedback": [
      {
        "user_type": "string",
        "raw_feedback": "string",
        "sentiment": "positive|neutral|negative",
        "tags_added": ["string"],
        "issues": ["string"],
        "poi_updates": [
          {
            "poi_id": "string",
            "field": "string",
            "delta_or_tag": "string"
          }
        ],
        "user_profile_updates": {
          "likes": ["string"],
          "dislikes": ["string"],
          "weight_changes": {"key": number}
        }
      }
    ]
  }
}

硬性生成要求：
1. 只生成 1 条 plan，不要生成 plans 数组。
2. plan 必须有 4-5 个 POI。
3. plan.route_edges 必须连接相邻 POI，数量至少为 POI 数量 - 1。
4. plan 至少 2 个 backup_plans。
5. plan 至少 2 条 sample_feedback。
6. 每个 POI 必须从 source_points 中选择。
7. 每个 POI 的 source_instance、source_feature、lon、lat 必须与所选 source_point 完全一致。
8. 同一条 plan 中不要重复使用同一个 source_instance。
9. POI 名称必须像真实深圳店铺名，自然接地气，风格多样。
10. 不要所有地点都完美，必须包含合理缺点。
11. 所有分数字段范围为 1.0-5.0。
12. 所有时间、预算、步行时长要自洽。
13. city 固定为"深圳"。

字段自洽要求：
1. 公园、Citywalk 的 min_spend 必须为 0。
2. 公园、Citywalk 通常 indoor=false，air_conditioning=false，wifi=false。
3. route_edges 的 from 和 to 必须引用当前 plan.pois 中真实存在的 POI id。
4. route_edges 必须按路线顺序连接相邻 POI。
"""


# ============================================================
# Naming quality checks (from main script)
# ============================================================

FAKE_NAME_TOKENS = [
    "悠然", "静心", "萌芽", "欢乐", "甜蜜", "星空", "时光", "阳光", "微风",
    "清心", "童趣", "奇幻", "绘梦", "乐享", "乐聚", "悠享", "棋乐无穷",
    "童话森林", "故事树", "月光", "梦幻", "温馨", "绿荫"
]

TEMPLATE_NAME_SUFFIXES = ["小屋", "工坊", "乐园", "空间", "天地", "驿站", "时光屋", "时光站"]

SHENZHEN_NAME_ANCHORS = [
    "蛇口", "南油", "后海", "科技园", "粤海", "白石洲", "华侨城", "侨城东",
    "车公庙", "岗厦", "皇岗村", "梅林", "八卦岭", "西丽", "宝安中心",
    "海上世界", "深圳湾", "壹方城", "福田中心", "南头", "南头古城", "侨香",
    "上沙", "下沙", "沙尾", "水围", "大冲", "深大", "高新园", "南山",
    "福田", "宝安", "罗湖", "盐田", "龙华", "前海", "沙井", "大芬"
]

LIFE_NAME_ANCHORS = [
    "阿", "老", "陈记", "李记", "张记", "王记", "刘记", "肥仔", "胖哥", "二姐",
    "茶档", "糖水铺", "小馆", "饭堂", "书局", "咖啡", "轻食", "剧场", "桌游吧",
    "买手店", "花房", "露台", "巷口", "楼下", "三楼", "二楼", "旧厂", "社区店",
    "B座", "9号", "7号", "Deli", "Room", "Cafe", "Coffee", "House",
    "烧烤", "火锅", "烤肉", "桑拿鸡", "鸡煲", "边炉", "大排档", "夜宵",
    "电竞", "网吧", "密室", "真人CS", "KTV", "洗浴", "汗蒸", "儿童乐园", "游乐园"
]


def has_quality_name_anchor(name: str) -> bool:
    if any(anchor in name for anchor in SHENZHEN_NAME_ANCHORS):
        return True
    if any(anchor in name for anchor in LIFE_NAME_ANCHORS):
        return True
    if re.search(r"[A-Za-z0-9]", name):
        return True
    if re.search(r"[一二三四五六七八九十]楼|[一二三四五六七八九十]号|[A-Z]座", name):
        return True
    return False


def validate_plan_quality(plan: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    pois = plan.get("pois", [])
    if not isinstance(pois, list):
        return errors

    names = [str(poi.get("name", "")).strip() for poi in pois if isinstance(poi, dict)]

    for name in names:
        if not name:
            continue
        bad_tokens = [token for token in FAKE_NAME_TOKENS if token in name]
        if bad_tokens:
            errors.append(f"POI name 有明显 AI 味：{name}，命中 {bad_tokens}")

        bad_suffixes = [
            suffix for suffix in TEMPLATE_NAME_SUFFIXES
            if name.endswith(suffix) and not (suffix == "乐园" and has_quality_name_anchor(name))
        ]
        if bad_suffixes:
            errors.append(f"POI name 使用模板化后缀：{name}")

    anchored_count = sum(1 for name in names if has_quality_name_anchor(name))
    required_anchored_count = min(3, len(names))
    if names and anchored_count < required_anchored_count:
        errors.append(
            f"POI name 深圳/生活化锚点不足：{anchored_count}/{len(names)}，"
            f"至少需要 {required_anchored_count} 个带地名、人名、楼层、数字、英文或口语化小店锚点"
        )

    return errors


# ============================================================
# JSON parsing
# ============================================================

def extract_json(text: str) -> Dict[str, Any]:
    text = text.strip()
    text = re.sub(r"^```json\s*", "", text)
    text = re.sub(r"^```\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("模型输出中没有找到完整 JSON 对象")
    candidate = text[start:end + 1]
    try:
        return json.loads(candidate)
    except json.JSONDecodeError as e:
        if repair_json is None:
            raise ValueError(f"JSON 解析失败：{e}")
    try:
        repaired = repair_json(candidate)
        return json.loads(repaired)
    except Exception as e:
        raise ValueError(f"JSON 修复失败：{e}")


def repair_json_with_llm(raw_text: str, error_message: str) -> str:
    repair_prompt = f"""
下面是一段模型生成的 JSON，但它不是合法 JSON。
解析错误：{error_message}
请你只做 JSON 格式修复，不要添加解释，不要使用 Markdown，不要改变字段含义，不要删除已有字段。
只返回修复后的完整 JSON 对象。
损坏 JSON 如下：
{raw_text}
"""
    return call_llm(repair_prompt)


# ============================================================
# LLM call
# ============================================================

def call_llm(prompt: str) -> str:
    kwargs: Dict[str, Any] = {
        "model": OPENAI_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.65,
        "max_tokens": MAX_TOKENS,
    }
    if USE_JSON_MODE:
        kwargs["response_format"] = {"type": "json_object"}
    response = client.chat.completions.create(**kwargs)
    content = response.choices[0].message.content
    if content is None:
        raise ValueError("模型返回内容为空")
    return content.strip()


# ============================================================
# Build prompt for supplement task
# ============================================================

def build_supplement_prompt(task_id: str, design: Dict[str, Any], candidate_points: List[Dict[str, Any]], previous_errors: Optional[List[str]] = None) -> str:
    registry = load_registry()
    used_names = registry.get("used_poi_names", [])
    used_names_sample = used_names[-80:] if len(used_names) > 80 else used_names
    previous_errors = previous_errors or []

    category_sequence = design["category_sequence"]
    poi_slots = design["poi_slots"]

    return f"""
请为以下补充任务生成 Local Activity Sandbox 数据。

任务 ID：{task_id}
路线：{design['route_prompt']}
类别顺序：{' -> '.join(category_sequence)}

POI 槽位设计：
{json.dumps(poi_slots, ensure_ascii=False, indent=2)}

必须反映的要求：
{json.dumps(design.get('must_reflect', []), ensure_ascii=False, indent=2)}

强制执行规则：
1. plan.pois 数量必须等于 category_sequence 数量（{len(category_sequence)} 个）。
2. plan.pois 的顺序必须完全等于 category_sequence。
3. 每个 POI 的 category 必须严格使用对应 slot 的 category。
4. 每个 POI 的 name 必须贴近对应 slot 的 name_hint，可以略微自然化，但不能换成其他风格。
5. 每个 POI 的 avg_stay_minutes、avg_price、description 要体现对应 slot 的 role。
6. route_edges 必须按这个固定顺序连接相邻 POI。

上一轮生成被质检驳回的问题如下。本轮必须逐条修正：
{json.dumps(previous_errors[:20], ensure_ascii=False, indent=2)}

可用 source_points 如下。
你必须从这些点中选择 {len(category_sequence)} 个作为 POI。
每个 POI 的 source_instance、source_feature、lon、lat 必须与所选 source_point 完全一致。

source_points:
{json.dumps(candidate_points, ensure_ascii=False, indent=2)}

以下 POI 名称已经用过，请不要重复：
{json.dumps(used_names_sample, ensure_ascii=False, indent=2)}

请特别注意：
1. 这次只生成 1 条 plan。
2. 每个 POI 都要有足够长的 description。
3. backup_plans 要体现动态重规划。
4. sample_feedback 要体现游后反馈闭环。
5. 数据要有真实决策冲突，不要让所有点都完美。
6. POI 名字要像真实深圳店名，自然多样，不要AI味。4-5个名字风格必须各不相同。
7. 如果你发现自己想写"悠然/静心/萌芽/欢乐/甜蜜/星空/时光/工坊/小屋/乐园/空间"，立刻换成更像深圳街巷小店的名字。

{SCHEMA_REQUIREMENT}
"""


# ============================================================
# Validation
# ============================================================

REQUIRED_POI_FIELDS = [
    "id", "source_instance", "source_feature", "name", "category", "city",
    "area", "lon", "lat", "address", "avg_price", "open_hours",
    "avg_stay_minutes", "reservation_required", "indoor", "weather_fit",
    "energy_level", "crowd_risk", "queue_risk", "mood_tags",
    "activity_tags", "suitable_for", "avoid_for", "photo_score",
    "conversation_score", "novelty_score", "relax_score", "facilities",
    "transportation", "business_rules", "community_feedback", "description"
]

REQUIRED_FACILITY_FIELDS = [
    "restroom", "pet_friendly", "charging_available", "wifi", "accessible",
    "baby_care_room", "luggage_storage", "air_conditioning", "seating_quality"
]

REQUIRED_TRANSPORTATION_FIELDS = [
    "subway", "subway_station", "subway_lines", "subway_exit",
    "subway_distance_meters", "subway_walk_minutes", "bus_distance_meters",
    "parking_available", "parking_fee", "bike_parking_available",
    "taxi_dropoff_friendly", "walking_difficulty"
]

REQUIRED_SUBWAY_FIELDS = [
    "nearest_station", "lines", "exit", "distance_meters", "walk_minutes",
    "recommended", "last_train_buffer_minutes", "access_note"
]

REQUIRED_BUSINESS_RULE_FIELDS = [
    "photo_allowed", "outside_food_allowed", "group_buy_available",
    "reservation_required", "takeaway_allowed", "refund_friendly", "min_spend",
    "time_limit_minutes", "age_restriction", "dress_code", "quiet_required",
    "pets_allowed_inside"
]

REQUIRED_COMMUNITY_FEEDBACK_FIELDS = [
    "feedback_count", "positive_rate", "common_praises", "common_issues",
    "tag_votes", "score_adjustments"
]

REQUIRED_SCORE_ADJUSTMENT_FIELDS = [
    "photo_score", "conversation_score", "novelty_score", "relax_score"
]

REQUIRED_EDGE_FIELDS = [
    "from", "to", "distance_meters", "walking_minutes", "cycling_minutes",
    "taxi_minutes", "subway_recommended", "subway_minutes",
    "subway_transfer_count", "transit_modes", "route_type", "scenic_score",
    "shade_score", "crowd_level", "suitable_weather", "energy_cost",
    "route_note"
]


def check_required_fields(obj: Dict[str, Any], fields: List[str], prefix: str, errors: List[str]) -> None:
    for field in fields:
        if field not in obj:
            errors.append(f"{prefix} 缺少字段：{field}")


def validate_task_data(data: Dict[str, Any], task_id: str, design: Dict[str, Any], candidate_points: List[Dict[str, Any]]) -> List[str]:
    errors: List[str] = []

    plan = data.get("plan")
    if not isinstance(plan, dict):
        errors.append("plan 必须是对象")
        return errors

    candidate_map = {int(p["source_instance"]): p for p in candidate_points}
    category_sequence = design["category_sequence"]
    pois = plan.get("pois", [])

    if not isinstance(pois, list):
        errors.append("plan.pois 必须是数组")
        return errors

    if len(pois) != len(category_sequence):
        errors.append(f"plan.pois 数量必须为 {len(category_sequence)}，实际为 {len(pois)}")

    categories = [str(poi.get("category", "")).strip() for poi in pois if isinstance(poi, dict)]
    if categories != category_sequence:
        errors.append(f"category 顺序不匹配：expected {' -> '.join(category_sequence)}，actual {' -> '.join(categories)}")

    poi_ids = set()
    for poi_index, poi in enumerate(pois, start=1):
        prefix = f"plan.pois[{poi_index}]"
        if not isinstance(poi, dict):
            errors.append(f"{prefix} 必须是对象")
            continue

        check_required_fields(poi, REQUIRED_POI_FIELDS, prefix, errors)

        poi_id = poi.get("id")
        if poi_id:
            if poi_id in poi_ids:
                errors.append(f"{prefix}.id 重复：{poi_id}")
            poi_ids.add(poi_id)

        if poi.get("city") != "深圳":
            errors.append(f"{prefix}.city 必须为 深圳")

        instance = poi.get("source_instance")
        try:
            instance_i = int(instance)
        except Exception:
            errors.append(f"{prefix}.source_instance 非法：{instance}")
            instance_i = None

        if instance_i is not None:
            if instance_i not in candidate_map:
                errors.append(f"{prefix}.source_instance 不在 candidate_points 中：{instance_i}")
            else:
                source_point = candidate_map[instance_i]
                if str(poi.get("source_feature")) != str(source_point["source_feature"]):
                    errors.append(f"{prefix}.source_feature 与 source_points 不一致")
                if abs(float(poi.get("lon", 0)) - float(source_point["lon"])) > 1e-8:
                    errors.append(f"{prefix}.lon 与 source_points 不一致")
                if abs(float(poi.get("lat", 0)) - float(source_point["lat"])) > 1e-8:
                    errors.append(f"{prefix}.lat 与 source_points 不一致")

        for score_field in ["photo_score", "conversation_score", "novelty_score", "relax_score"]:
            score = poi.get(score_field)
            if not isinstance(score, (int, float)):
                errors.append(f"{prefix}.{score_field} 必须是数字")
            elif not (1.0 <= float(score) <= 5.0):
                errors.append(f"{prefix}.{score_field} 不在 1.0-5.0 范围内：{score}")

        facilities = poi.get("facilities", {})
        if isinstance(facilities, dict):
            check_required_fields(facilities, REQUIRED_FACILITY_FIELDS, f"{prefix}.facilities", errors)

        transportation = poi.get("transportation", {})
        if isinstance(transportation, dict):
            check_required_fields(transportation, REQUIRED_TRANSPORTATION_FIELDS, f"{prefix}.transportation", errors)
            subway = transportation.get("subway", {})
            if isinstance(subway, dict):
                check_required_fields(subway, REQUIRED_SUBWAY_FIELDS, f"{prefix}.transportation.subway", errors)

        business_rules = poi.get("business_rules", {})
        if isinstance(business_rules, dict):
            check_required_fields(business_rules, REQUIRED_BUSINESS_RULE_FIELDS, f"{prefix}.business_rules", errors)

        community_feedback = poi.get("community_feedback", {})
        if isinstance(community_feedback, dict):
            check_required_fields(community_feedback, REQUIRED_COMMUNITY_FEEDBACK_FIELDS, f"{prefix}.community_feedback", errors)
            score_adjustments = community_feedback.get("score_adjustments", {})
            if isinstance(score_adjustments, dict):
                check_required_fields(score_adjustments, REQUIRED_SCORE_ADJUSTMENT_FIELDS, f"{prefix}.community_feedback.score_adjustments", errors)

        category = poi.get("category")
        if category in ["公园", "Citywalk"]:
            if poi.get("indoor") is not False:
                errors.append(f"{prefix}: {category} 通常应 indoor=false")
            if business_rules.get("min_spend") not in [0, None]:
                errors.append(f"{prefix}: {category} 的 min_spend 应为 0")

    edges = plan.get("route_edges", [])
    if not isinstance(edges, list):
        errors.append("plan.route_edges 必须是数组")
    elif len(edges) < max(0, len(pois) - 1):
        errors.append(f"plan.route_edges 数量不足，至少需要 {len(pois) - 1}")
    else:
        expected_pairs = [(pois[i].get("id"), pois[i+1].get("id")) for i in range(len(pois) - 1)]
        actual_pairs = []
        for edge in edges:
            if not isinstance(edge, dict):
                continue
            check_required_fields(edge, REQUIRED_EDGE_FIELDS, "plan.route_edges", errors)
            actual_pairs.append((edge.get("from"), edge.get("to")))
        for pair in expected_pairs:
            if pair not in actual_pairs:
                errors.append(f"plan.route_edges 缺少相邻连接：{pair[0]} -> {pair[1]}")

    backup_plans = plan.get("backup_plans", [])
    if not isinstance(backup_plans, list) or len(backup_plans) < 2:
        errors.append("plan.backup_plans 至少需要 2 条")

    sample_feedback = plan.get("sample_feedback", [])
    if not isinstance(sample_feedback, list) or len(sample_feedback) < 2:
        errors.append("plan.sample_feedback 至少需要 2 条")

    # Global dedup check
    registry = load_registry()
    used_instances = set(int(x) for x in registry.get("used_source_instances", []))
    used_names = set(str(x) for x in registry.get("used_poi_names", []))
    for poi in plan.get("pois", []):
        instance = poi.get("source_instance")
        if instance is not None:
            try:
                if int(instance) in used_instances:
                    errors.append(f"source_instance 全局重复：{int(instance)}")
            except Exception:
                pass
        name = poi.get("name")
        if name and str(name) in used_names:
            errors.append(f"POI name 全局重复：{name}")

    # Quality check
    errors.extend(validate_plan_quality(plan))

    return errors


def normalize_task_metadata(data: Dict[str, Any], task_id: str, design: Dict[str, Any]) -> None:
    data["task_id"] = task_id
    data["scene_id"] = "supplement"
    data["scene_name"] = "补充数据"
    data["target_user"] = "补充不足类别"
    data["route_index"] = 1
    data["route_style"] = design.get("route_prompt", "")
    plan = data.get("plan")
    if isinstance(plan, dict):
        plan["route_style"] = design.get("route_prompt", "")


# ============================================================
# Generate
# ============================================================

def generate_supplement(task_id: str, design: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    json_path = JSON_DIR / f"{task_id}.json"
    raw_path = RAW_DIR / f"{task_id}.txt"

    if json_path.exists():
        print(f"[SKIP] {task_id} 已存在")
        return json.loads(json_path.read_text(encoding="utf-8"))

    last_error = None
    previous_errors: List[str] = []

    for attempt in range(1, MAX_RETRY_PER_TASK + 2):
        print(f"[CALL] 生成补充任务：{task_id}，第 {attempt} 次尝试")

        try:
            candidate_points = sample_points_for_task(
                task_id=f"{task_id}_attempt_{attempt}",
                count=CANDIDATE_POINTS_PER_TASK,
            )
        except RuntimeError as e:
            print(f"[ERROR] {task_id}：{e}")
            return None

        prompt = build_supplement_prompt(task_id, design, candidate_points, previous_errors)

        try:
            raw_text = call_llm(prompt)
            raw_attempt_path = RAW_DIR / f"{task_id}_attempt_{attempt}.txt"
            raw_attempt_path.write_text(raw_text, encoding="utf-8")

            try:
                data = extract_json(raw_text)
            except Exception as parse_error:
                print(f"[WARN] JSON 解析失败，尝试修复：{parse_error}")
                repaired_text = repair_json_with_llm(raw_text, str(parse_error))
                data = extract_json(repaired_text)

            normalize_task_metadata(data, task_id, design)
            errors = validate_task_data(data, task_id, design, candidate_points)
            previous_errors = errors

            data["_meta"] = {
                "task_id": task_id,
                "scene_id": "supplement",
                "generated_at": datetime.now().isoformat(timespec="seconds"),
                "attempt": attempt,
                "validation_passed": len(errors) == 0,
                "validation_errors": errors,
                "candidate_source_instances": [p["source_instance"] for p in candidate_points],
            }

            if not errors:
                raw_path.write_text(raw_text, encoding="utf-8")
                json_path.write_text(
                    json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
                )
                update_registry_with_plan(data["plan"])
                print(f"[OK] {task_id} 校验通过")
                return data

            print(f"[WARN] {task_id} 校验失败，{len(errors)} 个问题")
            for err in errors[:10]:
                print(f"  - {err}")

            failed_path = JSON_DIR / f"{task_id}_failed_attempt_{attempt}.json"
            failed_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

        except Exception as e:
            last_error = str(e)
            previous_errors = [f"上一轮异常：{last_error}"]
            print(f"[ERROR] {task_id} 第 {attempt} 次失败：{e}")

        if attempt <= MAX_RETRY_PER_TASK:
            print(f"[WAIT] 等待 {CALL_DELAY_SECONDS} 秒...")
            time.sleep(CALL_DELAY_SECONDS)

    print(f"[FAILED] {task_id} 最终失败：{last_error}")
    return None


# ============================================================
# Main
# ============================================================

def main() -> None:
    print("========== 补充 POI 数据生成 ==========")
    print(f"模型：{OPENAI_MODEL}")
    print(f"Base URL：{OPENAI_BASE_URL}")
    print(f"输出目录：{OUTPUT_DIR.resolve()}")
    print(f"源点位数量：{len(SOURCE_POINTS)}")

    if not SUPPLEMENT_DESIGNS_FILE.exists():
        print(f"[ERROR] 补充路线设计文件不存在：{SUPPLEMENT_DESIGNS_FILE}")
        return

    designs = json.loads(SUPPLEMENT_DESIGNS_FILE.read_text(encoding="utf-8"))
    print(f"补充路线数：{len(designs)}")
    print("=" * 50)

    success_count = 0
    fail_count = 0

    for i, (task_id, design) in enumerate(designs.items(), 1):
        print(f"\n========== [{i}/{len(designs)}] {task_id} ==========")
        result = generate_supplement(task_id, design)
        if result:
            success_count += 1
        else:
            fail_count += 1

        if i < len(designs):
            print(f"[WAIT] 等待 {CALL_DELAY_SECONDS} 秒...")
            time.sleep(CALL_DELAY_SECONDS)

    print(f"\n========== 补充生成完成 ==========")
    print(f"成功：{success_count}，失败：{fail_count}")
    print(f"输出目录：{JSON_DIR}")


if __name__ == "__main__":
    main()
