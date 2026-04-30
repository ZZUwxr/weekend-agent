import json
import os
import random
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import argparse

import pandas as pd
from dotenv import load_dotenv
from openai import OpenAI

try:
    from json_repair import repair_json
except Exception:
    repair_json = None


# ============================================================
# 配置
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

client = OpenAI(
    api_key=OPENAI_API_KEY,
    base_url=OPENAI_BASE_URL
)

OUTPUT_DIR = Path("generated_route_packs_30calls")
RAW_DIR = OUTPUT_DIR / "raw"
JSON_DIR = OUTPUT_DIR / "json"
LOG_DIR = OUTPUT_DIR / "logs"
PROMPT_DIR = SCRIPT_DIR / "prompt"
ROUTE_DESIGNS_FILE = PROMPT_DIR / "route_designs.json"

RAW_DIR.mkdir(parents=True, exist_ok=True)
JSON_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

REGISTRY_FILE = OUTPUT_DIR / "used_registry.json"
MERGED_FILE = OUTPUT_DIR / "all_route_packs.json"
VALIDATION_REPORT_FILE = OUTPUT_DIR / "validation_report.json"
FAILED_TASKS_FILE = OUTPUT_DIR / "failed_tasks.json"

RANDOM_SEED = 42
MAX_RETRY_PER_TASK = int(os.getenv("MAX_RETRY_PER_TASK", "2"))

random.seed(RANDOM_SEED)


# ============================================================
# 场景配置：10 个场景 × 每个 3 条路线 = 30 个任务
# ============================================================

SCENES: List[Dict[str, Any]] = [
    {
        "scene_id": "parent_child",
        "scene_name": "亲子陪伴",
        "target_user": "带 3-10 岁孩子周末出门的家长",
        "route_styles": [
            "轻松半日亲子路线",
            "雨天室内亲子路线",
            "低强度户外亲子路线"
        ],
        "must_have": [
            "路线需要考虑卫生间、无障碍、休息座位、孩子体力",
            "路线不能过度依赖长距离步行",
            "至少部分 POI 应具备 restroom、accessible 或 baby_care_room",
            '路线中至少 1 个 POI 的 suitable_for 包含"亲子"',
            "亲子半日/雨天路线可以让游乐园、儿童乐园、亲子馆或大型室内乐园占据 180 分钟以上"
        ],
        "avoid": [
            "高强度运动",
            "太吵或成人化的夜间活动",
            "路线总步行时间过长"
        ]
    },
    {
        "scene_id": "friends",
        "scene_name": "朋友聚会",
        "target_user": "三五好友周末想聚一聚，重视聊天、互动和新鲜感",
        "route_styles": [
            "聊天放松路线",
            "高互动朋友路线",
            "夜间桌游甜品路线"
        ],
        "must_have": [
            '至少 2 个地点 conversation_score >= 4.2 或 activity_tags 包含"互动"',
            "需要兼顾吃喝、聊天、娱乐",
            "可以包含烧烤、火锅、烤肉、桑拿鸡、网吧/电竞、密室逃脱、真人CS、KTV、桌游、夜宵、糖水"
        ],
        "avoid": [
            "过于安静导致无法社交",
            "单人向地点过多",
            "路线风格太散"
        ]
    },
    {
        "scene_id": "family",
        "scene_name": "家人同行",
        "target_user": "和父母、长辈或家庭成员一起周末出门",
        "route_styles": [
            "长辈友好轻松路线",
            "家庭聚餐散步路线",
            "低步行室内路线"
        ],
        "must_have": [
            "total_walking_minutes <= 40",
            "POI 的 transportation.walking_difficulty 不能为 high",
            "至少 2 个地点 accessible=true",
            "需要考虑停车、地铁距离、卫生间、座位舒适度"
        ],
        "avoid": [
            "太吵",
            "太潮流但长辈难接受",
            "需要剧烈运动",
            "停车困难且地铁又远"
        ]
    },
    {
        "scene_id": "couple_date",
        "scene_name": "情侣约会",
        "target_user": "情侣周末约会，重视氛围、拍照、聊天和体验感",
        "route_styles": [
            "傍晚松弛约会路线",
            "拍照看展约会路线",
            "安静聊天收尾路线"
        ],
        "must_have": [
            "平均 photo_score 或 conversation_score >= 4.3",
            "至少 1 个地点适合拍照",
            "至少 1 个地点适合安静聊天",
            "路线需要有自然节奏：开场、主活动、收尾"
        ],
        "avoid": [
            "过于吵闹",
            "太多亲子或多人团建地点",
            "每个地点都像普通餐饮，缺少约会感"
        ]
    },
    {
        "scene_id": "solo_relax",
        "scene_name": "独处放松",
        "target_user": "一个人周末想慢下来，放松、读书、喝咖啡、轻度散步",
        "route_styles": [
            "一个人慢逛路线",
            "咖啡书店放空路线",
            "低刺激治愈路线"
        ],
        "must_have": [
            "energy_level 平均值 <= 1.7",
            '至少 2 个地点 mood_tags 包含"安静"或"松弛"',
            "地点需要适合独处，不需要强社交",
            "路线节奏要轻，避免赶场"
        ],
        "avoid": [
            "桌游、多人互动、强社交",
            "排队风险过高",
            "过度消费"
        ]
    },
    {
        "scene_id": "pet_friendly",
        "scene_name": "宠物友好",
        "target_user": "带宠物出门的用户，需要宠物友好、户外或允许宠物进入",
        "route_styles": [
            "宠物散步咖啡路线",
            "户外轻松陪伴路线",
            "宠物友好低预算路线"
        ],
        "must_have": [
            "至少 2 个地点 facilities.pet_friendly=true 或 business_rules.pets_allowed_inside=true",
            "需要说明哪些地点宠物可进入，哪些只能户外停留",
            "至少 1 个地点为公园或 Citywalk",
            "需要考虑饮水、休息、路线强度"
        ],
        "avoid": [
            "全是不可携宠的室内地点",
            "过长步行",
            "拥挤风险过高"
        ]
    },
    {
        "scene_id": "rainy_indoor",
        "scene_name": "雨天室内",
        "target_user": "下雨天也想出门，但希望全程室内、少走路、不狼狈",
        "route_styles": [
            "雨天看展咖啡路线",
            "雨天书店手作路线",
            "雨天低步行室内路线"
        ],
        "must_have": [
            "所有 POI indoor 必须为 true",
            '所有 POI weather_fit 必须包含"雨天"',
            "需要考虑地铁距离或打车友好",
            "可以包含展览、书店、咖啡、手作、商场餐饮、KTV、电竞馆、室内运动、室内儿童乐园等室内组合"
        ],
        "avoid": [
            "公园",
            "纯户外 Citywalk",
            "雨天不友好的露天路线"
        ]
    },
    {
        "scene_id": "low_budget",
        "scene_name": "低预算闲逛",
        "target_user": "预算有限但想周末出门透气，追求低成本、可执行",
        "route_styles": [
            "百元内城市漫游",
            "免费公园书店路线",
            "低价甜品散步路线"
        ],
        "must_have": [
            "total_budget <= 120",
            "至少 1 个免费 POI",
            "合理使用公园、Citywalk、书店、低价甜品、低价咖啡",
            "要标注哪些消费是可选的"
        ],
        "avoid": [
            "高价手作",
            "小剧场高票价",
            "最低消费过高",
            "总预算虚高"
        ]
    },
    {
        "scene_id": "photo_checkin",
        "scene_name": "拍照打卡",
        "target_user": "喜欢拍照、发朋友圈、小红书风格打卡的用户",
        "route_styles": [
            "高颜值拍照路线",
            "展览甜品打卡路线",
            "城市街区出片路线"
        ],
        "must_have": [
            "平均 photo_score >= 4.5",
            "至少 2 个地点 business_rules.photo_allowed=true",
            "需要包含拍照风格差异：展览、甜品、街区、买手店、公园等",
            "需要提醒不可拍摄或不可闪光的规则"
        ],
        "avoid": [
            "photo_allowed=false 的地点过多",
            "灯光差、拥挤风险高但没有替代方案",
            "全是同质化甜品店"
        ]
    },
    {
        "scene_id": "night_gathering",
        "scene_name": "夜间小聚",
        "target_user": "晚上下班后或周末夜间想和朋友轻松聚一下",
        "route_styles": [
            "夜间聊天甜品路线",
            "桌游轻食朋友局",
            "小剧场茶馆收尾路线"
        ],
        "must_have": [
            "至少 2 个 POI 营业到 22:00 以后",
            "需要考虑夜间打车、地铁距离、安全感",
            "可以包含烧烤、火锅、烤肉、桑拿鸡、桌游、电竞馆、网吧、KTV、甜品、茶馆、夜宵、小剧场",
            "路线不能默认用户愿意高消费"
        ],
        "avoid": [
            "全部 18:00 关门的地点",
            "夜间过长步行",
            "过于吵闹且没有安静替代方案"
        ]
    }
]


def build_plan_tasks() -> List[Dict[str, Any]]:
    tasks = []
    for scene in SCENES:
        for idx, route_style in enumerate(scene["route_styles"], start=1):
            tasks.append({
                "task_id": f"{scene['scene_id']}_{idx}",
                "scene_id": scene["scene_id"],
                "scene_name": scene["scene_name"],
                "target_user": scene["target_user"],
                "route_index": idx,
                "route_style": route_style,
                "must_have": scene["must_have"],
                "avoid": scene["avoid"]
            })
    return tasks


# ============================================================
# 读取 CSV / Excel 源点位
# ============================================================

def load_source_points() -> List[Dict[str, Any]]:
    if not SOURCE_POINTS_FILE:
        raise RuntimeError("请在 .env 中设置 SOURCE_POINTS_FILE，例如 ./points.csv")

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
        raise ValueError(f"源点位文件缺少列：{missing}，当前列名：{list(df.columns)}")

    df = df.dropna(subset=["Lon", "Lat"]).copy()

    points = []
    for _, row in df.iterrows():
        points.append({
            "source_feature": str(row["Feature"]).strip(),
            "source_instance": int(row["Instance"]),
            "lon": float(row["Lon"]),
            "lat": float(row["Lat"])
        })

    if not points:
        raise RuntimeError("源点位为空")

    print(f"[INFO] 已读取源点位 {len(points)} 个。")
    return points


SOURCE_POINTS = load_source_points()


# ============================================================
# Registry：全局去重
# ============================================================

def load_registry() -> Dict[str, Any]:
    if not REGISTRY_FILE.exists():
        return {
            "used_source_instances": [],
            "used_poi_names": [],
            "updated_at": None
        }

    with REGISTRY_FILE.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_registry(registry: Dict[str, Any]) -> None:
    registry["updated_at"] = datetime.now().isoformat(timespec="seconds")
    REGISTRY_FILE.write_text(
        json.dumps(registry, ensure_ascii=False, indent=2),
        encoding="utf-8"
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


def rebuild_registry_from_existing_outputs() -> None:
    """
    断点续跑时，根据已成功生成的 JSON 重建全局 registry。
    """
    registry = {
        "used_source_instances": [],
        "used_poi_names": [],
        "updated_at": None
    }

    used_instances = set()
    used_names = set()

    for path in sorted(JSON_DIR.glob("*.json")):
        if "_failed_attempt_" in path.name:
            continue

        try:
            with path.open("r", encoding="utf-8") as f:
                data = json.load(f)
            plan = data.get("plan", {})
            for poi in plan.get("pois", []):
                if "source_instance" in poi:
                    used_instances.add(int(poi["source_instance"]))
                if "name" in poi:
                    used_names.add(str(poi["name"]))
        except Exception:
            continue

    registry["used_source_instances"] = sorted(list(used_instances))
    registry["used_poi_names"] = sorted(list(used_names))
    save_registry(registry)


def sample_points_for_task(task_id: str, count: int) -> List[Dict[str, Any]]:
    registry = load_registry()
    used_instances = set(int(x) for x in registry.get("used_source_instances", []))

    available_points = [
        p for p in SOURCE_POINTS
        if int(p["source_instance"]) not in used_instances
    ]

    if len(available_points) < count:
        raise RuntimeError(f"可用 source_points 不足。剩余 {len(available_points)}，需要 {count}")

    random.seed(f"{RANDOM_SEED}_{task_id}")
    return random.sample(available_points, count)


# ============================================================
# Prompt
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
- "游乐园"可以作为真实亲子大项目出现，但名字要像商场/街区里的真实点位，例如"龙华壹方城儿童乐园"，不要写成"欢乐亲子乐园"。
- 禁止所有名字都是"形容词+名词+品类"的固定结构。
- 禁止名字像景区宣传语或儿童绘本标题，例如"童话森林书店"、"故事树咖啡馆"。

每条路线的 4-5 个 POI 名字风格必须各不相同；至少 3 个名字要带有深圳地名、街巷楼层、人名昵称、数字、英文或口语化小店锚点之一。

【路线多样性要求】
不同路线的节奏和结构必须有明显差异，不能都是"公园→咖啡→手作→甜品"这种套路。
你要先在脑中选一个路线骨架，再填 POI：
- 饭局开场型：正餐/轻食开始，再转聊天或活动，最后短停留收尾。
- 单核心辐射型：围绕商场、创意园、书店、剧场或海边片区展开，少移动但体验变化明显。
- 街巷漫游型：Citywalk/公园/街区作为主线，中途只插入 1-2 个休息点。
- 体验优先型：桌游、网吧/电竞、密室逃脱、真人CS、KTV、运动、手作、小剧场或亲子体验是核心，不要让咖啡甜品喧宾夺主。
- 夜间收口型：晚饭或桌游后，用茶馆、糖水、打车点或小剧场收尾。
- 朋友放松型：可以是上网、密室、真人CS、烧烤、火锅、烤肉、桑拿鸡、糖水、夜宵，不要总是咖啡甜品。
- 亲子大项目型：一个游乐园、儿童乐园、亲子馆或大型室内乐园可以占据 180-360 分钟，其他 POI 只是进场前吃饭、午后补水、离场休息或打车点。

同一批任务里不要重复同一个 category 顺序；不要连续多条路线都使用"咖啡/书店/手作/甜品"这组安全组合。
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
          "tag_votes": {
            "tag": number
          },
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
          "weight_changes": {
            "key": number
          }
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
9. POI 名称必须像真实深圳店铺名，自然接地气，风格多样（品牌风、地名风、人名风、直白风、中英混搭等），禁止使用"悠然/静心/萌芽/欢乐/甜蜜/星空/时光"等AI味浓重的形容词。
10. 不要所有地点都完美，必须包含合理缺点，例如周末人多、停车难、不可拍照、需要预约、最低消费、不可携宠等。
11. 所有分数字段范围为 1.0-5.0。
12. 所有时间、预算、步行时长要自洽。
13. city 固定为"深圳"。

字段自洽要求：
1. 公园、Citywalk 的 min_spend 必须为 0。
2. 公园、Citywalk 通常 indoor=false，air_conditioning=false，wifi=false。
3. 公园可 outside_food_allowed=true，但 takeaway_allowed=false。
4. 雨天室内场景中所有 POI 必须 indoor=true 且 weather_fit 包含"雨天"。
5. 亲子场景中至少部分 POI 应具备 restroom、accessible 或 baby_care_room。
6. 宠物友好场景中至少部分 POI facilities.pet_friendly=true 或 business_rules.pets_allowed_inside=true。
7. 夜间场景中至少 2 个 POI 的 open_hours 应晚于 22:00。
8. 低预算场景 total_budget <= 120，且至少包含一个 avg_price=0 的 POI。
9. route_edges 的 from 和 to 必须引用当前 plan.pois 中真实存在的 POI id。
10. route_edges 必须按路线顺序连接相邻 POI。
"""


ROUTE_BLUEPRINTS: Dict[str, Dict[str, Any]] = {
    "parent_child_1": {
        "structure": "进场前补给 -> 游乐园/亲子馆作为 180-300 分钟核心 -> 离场休息 -> 打车友好收尾",
        "category_hint": "游乐园/亲子空间必须承担主活动，轻食/甜品/书店只是辅助，不要平均分配停留时间",
        "avoid_sequence": "公园 -> 咖啡 -> 手作 -> 甜品",
        "tone": "像真实带娃半日出门：一个主场玩够，家长考虑厕所、座位、补水和孩子崩溃点。"
    },
    "parent_child_2": {
        "structure": "全室内单核心辐射：商场儿童乐园/亲子馆长停留，吃喝和休息在同楼或连廊内完成",
        "category_hint": "游乐园/亲子空间/展览 + 餐厅/甜品/书店，不放户外点",
        "avoid_sequence": "任何露天公园或长距离 Citywalk",
        "tone": "雨天不狼狈，卫生间和电梯比拍照更重要。"
    },
    "parent_child_3": {
        "structure": "户外短段主线 -> 可坐下的亲子补给 -> 早结束",
        "category_hint": "公园/Citywalk 只能作为短段，后接轻食/社区咖啡/书店",
        "avoid_sequence": "连续两个高消耗户外点",
        "tone": "孩子能放电，但总步行和排队都要克制。"
    },
    "friends_1": {
        "structure": "真实朋友局：火锅/烤肉/烧烤/桑拿鸡开场 -> 茶档或糖水聊天 -> 可选上网/桌游/夜宵收尾",
        "category_hint": "烧烤/火锅/烤肉/桑拿鸡/餐厅 + 茶馆/甜品 + 桌游/电竞馆/网吧",
        "avoid_sequence": "手作 -> 桌游 -> 轻食 -> 甜品",
        "tone": "重点是坐得住、聊得开，像男生或老朋友真的会约的局，不靠打卡撑内容。"
    },
    "friends_2": {
        "structure": "互动项目直接开场 -> 中途硬核补给 -> 第二个互动或夜间活动",
        "category_hint": "密室逃脱/真人CS/电竞馆/网吧/桌游/运动/KTV 至少两个，火锅/烧烤/烤肉只是承接",
        "avoid_sequence": "咖啡甜品堆叠",
        "tone": "强互动，有输赢、肾上腺素或共同任务，但预留冷静聊天点。"
    },
    "friends_3": {
        "structure": "晚饭/烧烤/火锅 -> 桌游或上网长停留 -> 糖水/茶档/夜宵收尾 -> 打车友好",
        "category_hint": "烧烤/火锅/烤肉/餐厅 + 桌游/电竞馆/网吧 + 甜品/茶馆/夜间活动",
        "avoid_sequence": "白天书店公园路线",
        "tone": "夜间真实可执行，不要默认高消费。"
    },
    "family_1": {
        "structure": "停车/地铁方便开场 -> 坐下喝茶或吃饭 -> 低步行观赏 -> 早收尾",
        "category_hint": "茶馆/餐厅 + 展览/书店 + 短距离公园或商场内点",
        "avoid_sequence": "手作和潮流店过多",
        "tone": "长辈舒服优先，椅子、厕所、噪音、停车都要写清。"
    },
    "family_2": {
        "structure": "家庭正餐为核心 -> 饭后 15-25 分钟散步 -> 甜品/茶水收口",
        "category_hint": "餐厅必须是核心，Citywalk/公园只承担饭后消食",
        "avoid_sequence": "先公园再茶馆再手作",
        "tone": "像真实家庭周末，不追求新奇但要顺路。"
    },
    "family_3": {
        "structure": "全程低步行室内串联，必要时可打车一段",
        "category_hint": "商场内餐饮/书店/展览/茶馆，强调电梯和座位",
        "avoid_sequence": "任何 walking_difficulty=high 的点",
        "tone": "适合腿脚一般或怕热怕雨的家人同行。"
    },
    "couple_date_1": {
        "structure": "傍晚海边/街区散步 -> 火锅/烤肉/茶室等明确约会主场 -> 夜景或安静收尾",
        "category_hint": "Citywalk/展览/买手店 + 餐厅/火锅/烤肉/茶馆 + 夜间休息点",
        "avoid_sequence": "亲子空间、桌游、过度嘈杂店",
        "tone": "松弛、有聊天空间，不要每个点都打卡。"
    },
    "couple_date_2": {
        "structure": "拍照主点 -> 低噪声补给 -> 展览/街区二次拍照 -> 收尾",
        "category_hint": "展览/买手店/Citywalk/甜品中选，但风格要错开",
        "avoid_sequence": "全是甜品店",
        "tone": "照片风格要不同，提醒拍摄限制。"
    },
    "couple_date_3": {
        "structure": "书店或展览开场 -> 茶/咖啡深聊 -> 短步行消化 -> 安静结束",
        "category_hint": "书店/展览 + 茶馆/咖啡 + 短 Citywalk",
        "avoid_sequence": "饭店堆叠或多人团建项目",
        "tone": "把对话质量放在第一位。"
    },
    "solo_relax_1": {
        "structure": "一个人慢逛 -> 非社交长停留 -> 简单吃饭或洗浴汗蒸放松 -> 可随时撤退",
        "category_hint": "书店/咖啡/Citywalk/公园/洗浴汗蒸，避免桌游和强互动",
        "avoid_sequence": "高能量体验项目",
        "tone": "没有打卡压力，允许中途发呆。"
    },
    "solo_relax_2": {
        "structure": "咖啡长坐 -> 书店或展览慢看 -> 简单轻食",
        "category_hint": "咖啡和书店是核心，但不要再塞手作甜品套路",
        "avoid_sequence": "咖啡 -> 书店 -> 手作 -> 甜品",
        "tone": "低刺激，停留时间长，移动少。"
    },
    "solo_relax_3": {
        "structure": "低噪声室内为主 -> 短距离补给 -> 早回家",
        "category_hint": "茶馆/书店/轻食/展览，所有点都要能独处",
        "avoid_sequence": "多人活动或夜间吵闹点",
        "tone": "治愈但不文艺腔，消费要克制。"
    },
    "pet_friendly_1": {
        "structure": "宠物可活动户外 -> 外摆咖啡/轻食 -> 宠物友好短逛或营地式停留",
        "category_hint": "公园/Citywalk + pet-friendly 咖啡/轻食/餐厅外摆 + 户外收尾",
        "avoid_sequence": "全室内不可携宠",
        "tone": "清楚写宠物能进室内还是只能外摆。"
    },
    "pet_friendly_2": {
        "structure": "户外陪伴主线，中间只安排一个补给点",
        "category_hint": "公园/Citywalk 是主角，补给点少而近",
        "avoid_sequence": "长距离暴走",
        "tone": "考虑饮水、阴凉、牵引绳和拥挤风险。"
    },
    "pet_friendly_3": {
        "structure": "低预算户外 -> 可选消费 -> 快速回撤",
        "category_hint": "免费公园/Citywalk + 低价外摆/便利补给",
        "avoid_sequence": "高价手作或室内店",
        "tone": "把可选消费和必须消费分开。"
    },
    "rainy_indoor_1": {
        "structure": "地铁直达室内展览 -> 同楼咖啡/轻食 -> 室内书店或买手店",
        "category_hint": "展览为核心，所有点 indoor=true",
        "avoid_sequence": "任何公园或露天街区",
        "tone": "雨天少撑伞，重视连廊、电梯、打车点。"
    },
    "rainy_indoor_2": {
        "structure": "书店长停留 -> 手作/小展 -> 糖水或茶水收尾",
        "category_hint": "书店和手作是核心，但名字不能叫工坊",
        "avoid_sequence": "户外 Citywalk",
        "tone": "适合雨天慢消磨，不赶场。"
    },
    "rainy_indoor_3": {
        "structure": "商场/园区内低步行三点串联，必要时只移动一层楼",
        "category_hint": "餐饮/咖啡/展览/买手店，距离短",
        "avoid_sequence": "跨区换乘",
        "tone": "把不狼狈和低步行放在第一位。"
    },
    "low_budget_1": {
        "structure": "免费街区漫游 -> 低价小吃/糖水 -> 免费公共空间收尾",
        "category_hint": "Citywalk/公园 + 低价甜品/轻食 + 书店或公共点",
        "avoid_sequence": "收费展览和手作",
        "tone": "总预算必须可信，不把可选消费算成必选。"
    },
    "low_budget_2": {
        "structure": "免费公园或书店为核心，消费点最多两个",
        "category_hint": "公园/书店 + 低价咖啡/糖水",
        "avoid_sequence": "连续四个消费点",
        "tone": "像真的省钱周末，而不是低价版约会路线。"
    },
    "low_budget_3": {
        "structure": "低价甜品开场 -> 近距离街巷散步 -> 可不消费收尾",
        "category_hint": "甜品 + Citywalk/公园 + 免费书店/公共点",
        "avoid_sequence": "高价咖啡和小剧场",
        "tone": "小确幸但不装精致。"
    },
    "photo_checkin_1": {
        "structure": "高颜值主拍点 -> 风格不同的二拍点 -> 补妆/休息 -> 收尾",
        "category_hint": "展览/买手店/Citywalk/公园组合，拍照风格必须不同",
        "avoid_sequence": "全甜品或全展览",
        "tone": "写清光线、人流、禁拍和备选角度。"
    },
    "photo_checkin_2": {
        "structure": "展览拍照 -> 甜品补给 -> 买手店或街区补镜头",
        "category_hint": "展览 + 甜品 + 买手店/Citywalk",
        "avoid_sequence": "同质化甜品店连排",
        "tone": "每个点承担不同照片素材。"
    },
    "photo_checkin_3": {
        "structure": "城市街区为主线，插入一个室内休息点",
        "category_hint": "Citywalk/公园/买手店 + 咖啡或甜品",
        "avoid_sequence": "室内点过多",
        "tone": "强调街景、橱窗、转角和天气风险。"
    },
    "night_gathering_1": {
        "structure": "晚饭/烧烤/火锅/桑拿鸡 -> 糖水或茶档深聊 -> 打车点收尾",
        "category_hint": "餐厅/烧烤/火锅/烤肉/桑拿鸡 + 甜品/茶馆 + 夜间活动",
        "avoid_sequence": "18:00 关门的白天点",
        "tone": "夜间安全、地铁末班和打车便利必须写清。"
    },
    "night_gathering_2": {
        "structure": "桌游/电竞/网吧长停留为核心 -> 烧烤或夜宵补给 -> 夜间糖水收尾",
        "category_hint": "桌游/电竞馆/网吧 + 烧烤/餐厅 + 甜品/茶馆",
        "avoid_sequence": "书店公园白天路线",
        "tone": "朋友局要真实，有噪音、低消、预约等冲突。"
    },
    "night_gathering_3": {
        "structure": "小剧场/演出 -> 茶馆复盘聊天 -> 短距离打车离开",
        "category_hint": "小剧场 + 茶馆/甜品 + 夜间活动",
        "avoid_sequence": "桌游甜品重复路线",
        "tone": "演出结束后的时间、交通和预算要自洽。"
    },
}


SCENE_REALITY_GUIDES: Dict[str, List[str]] = {
    "parent_child": [
        "深圳亲子周末常见是室内儿童乐园、商场亲子馆、主题游乐场、科学馆/展馆、户外无动力乐园；一个主场可以玩 3-6 小时。",
        "真实痛点是排队、午睡、补水、厕所、婴儿护理室、停车、电梯、孩子太累后快速撤退。",
        "不要把亲子路线切成很多浅尝辄止的咖啡/书店点；更像一整下午围绕一个乐园或亲子馆。"
    ],
    "friends": [
        "朋友聚会可以很生活化：烧烤、火锅、烤肉、桑拿鸡、夜宵、糖水、网吧/电竞、密室逃脱、真人CS、KTV、桌游。",
        "朋友局的核心不是文艺打卡，而是坐得住、能聊天、有输赢互动、能一起吐槽，预算和低消要真实。",
        "男生朋友或老同学路线可以更粗粝：先吃重口味正餐，再上网/密室/桌游，最后糖水或夜宵散场。"
    ],
    "family": [
        "家人同行更像吃一顿稳妥正餐、喝茶、饭后短散步、看展或商场内休息；长辈关心厕所、座位、停车和噪音。",
        "不要堆潮流店；家庭路线可以普通但顺路，步行少比新奇更重要。"
    ],
    "couple_date": [
        "情侣约会可以是海边/街区散步、展览、买手店、茶室、火锅烤肉、夜景，不必总是甜品咖啡。",
        "要体现开场破冰、核心共同体验、安静聊天收尾；照片风格和对话空间都要有。"
    ],
    "solo_relax": [
        "独处放松可以是书店、咖啡、展览、公园慢走、一个人吃简餐、洗浴汗蒸；重点是低社交压力和可随时撤退。",
        "不要安排强互动项目，不要赶场。"
    ],
    "pet_friendly": [
        "带宠常见是宠物友好公园、社区宠物活动区、户外市集、外摆咖啡/餐厅、营地式短停留。",
        "必须写清宠物能否进室内、是否只能外摆、饮水、阴凉、牵引绳和拥挤风险。"
    ],
    "rainy_indoor": [
        "雨天室内路线应像商场/园区内解决：室内展览、书店、手作、餐饮、买手店、儿童乐园、地铁连廊。",
        "核心是不撑伞少换乘，路线可以同楼层或同商场内短距离移动。"
    ],
    "low_budget": [
        "低预算不是低配精致约会，而是免费公园/街区/书店 + 一两个低价糖水、小吃、便利补给。",
        "要区分必选消费和可选消费，避免把付费展览/手作塞进百元路线。"
    ],
    "photo_checkin": [
        "拍照打卡要有不同素材：海边、街区、橱窗、展览、买手店、甜品、天台、夜景；不要全是同质甜品。",
        "必须写清光线、人流、禁拍/不可闪光、雨天替代角度。"
    ],
    "night_gathering": [
        "夜间小聚可以是烧烤、火锅、烤肉、桑拿鸡、桌游、电竞、网吧、KTV、小剧场、糖水、茶档、夜宵。",
        "必须考虑 22:00 后营业、地铁末班、打车点、安全感、低消和噪音。"
    ],
}


def get_route_blueprint(task_id: str) -> Dict[str, Any]:
    return ROUTE_BLUEPRINTS.get(task_id, {})


def get_scene_reality_guide(scene_id: str) -> List[str]:
    return SCENE_REALITY_GUIDES.get(scene_id, [])


_ROUTE_DESIGNS_CACHE: Optional[Dict[str, Dict[str, Any]]] = None


def load_route_designs() -> Dict[str, Dict[str, Any]]:
    global _ROUTE_DESIGNS_CACHE
    if _ROUTE_DESIGNS_CACHE is not None:
        return _ROUTE_DESIGNS_CACHE

    if not ROUTE_DESIGNS_FILE.exists():
        raise RuntimeError(f"固定路线 prompt 文件不存在：{ROUTE_DESIGNS_FILE}")

    with ROUTE_DESIGNS_FILE.open("r", encoding="utf-8") as f:
        designs = json.load(f)

    if not isinstance(designs, dict):
        raise ValueError(f"固定路线 prompt 文件必须是对象：{ROUTE_DESIGNS_FILE}")

    tasks = build_plan_tasks()
    expected_task_ids = {task["task_id"] for task in tasks}
    actual_task_ids = set(designs.keys())
    missing = sorted(expected_task_ids - actual_task_ids)
    extra = sorted(actual_task_ids - expected_task_ids)
    if missing:
        raise ValueError(f"固定路线 prompt 缺少任务：{missing}")
    if extra:
        raise ValueError(f"固定路线 prompt 包含未知任务：{extra}")

    for task_id, design in designs.items():
        if not isinstance(design, dict):
            raise ValueError(f"{task_id} 的固定路线 prompt 必须是对象")

        category_sequence = design.get("category_sequence")
        poi_slots = design.get("poi_slots")
        if not isinstance(category_sequence, list) or not (4 <= len(category_sequence) <= 5):
            raise ValueError(f"{task_id}.category_sequence 必须是 4-5 个类别")
        if not isinstance(poi_slots, list) or len(poi_slots) != len(category_sequence):
            raise ValueError(f"{task_id}.poi_slots 数量必须等于 category_sequence")

        slot_categories = [slot.get("category") for slot in poi_slots if isinstance(slot, dict)]
        if slot_categories != category_sequence:
            raise ValueError(f"{task_id}.poi_slots.category 必须与 category_sequence 完全一致")

    _ROUTE_DESIGNS_CACHE = designs
    return designs


def get_route_design(task_id: str) -> Dict[str, Any]:
    designs = load_route_designs()
    return designs[task_id]


def route_signature_from_plan(plan: Dict[str, Any]) -> str:
    categories = [
        str(poi.get("category", "")).strip()
        for poi in plan.get("pois", [])
        if isinstance(poi, dict)
    ]
    return " -> ".join(category for category in categories if category)


def load_recent_route_signatures(exclude_task_id: Optional[str] = None, limit: int = 12) -> List[str]:
    signatures: List[str] = []
    if not JSON_DIR.exists():
        return signatures

    for path in sorted(JSON_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
        if "_failed_attempt_" in path.name:
            continue

        try:
            with path.open("r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            continue

        if exclude_task_id and data.get("task_id") == exclude_task_id:
            continue

        signature = route_signature_from_plan(data.get("plan", {}))
        if signature and signature not in signatures:
            signatures.append(signature)

        if len(signatures) >= limit:
            break

    return signatures


FAKE_NAME_TOKENS = [
    "悠然", "静心", "萌芽", "欢乐", "甜蜜", "星空", "时光", "阳光", "微风",
    "清心", "童趣", "奇幻", "绘梦", "乐享", "乐聚", "悠享", "棋乐无穷",
    "童话森林", "故事树", "月光", "梦幻", "温馨", "绿荫"
]

TEMPLATE_NAME_SUFFIXES = [
    "小屋", "工坊", "乐园", "空间", "天地", "驿站", "时光屋", "时光站"
]

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

OVERUSED_CATEGORY_SEQUENCES = [
    ["公园", "咖啡", "手作体验", "甜品"],
    ["咖啡", "书店", "手作体验", "甜品"],
    ["轻食", "桌游", "手作体验", "甜品"],
    ["公园", "茶馆", "手作体验", "甜品"],
]

FRIEND_REAL_LIFE_CATEGORIES = {
    "烧烤", "火锅", "烤肉", "桑拿鸡", "电竞馆", "网吧", "密室逃脱",
    "真人CS", "KTV", "桌游", "运动", "夜间活动"
}


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


def validate_plan_quality(plan: Dict[str, Any], task: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    pois = plan.get("pois", [])
    if not isinstance(pois, list):
        return errors

    names = [str(poi.get("name", "")).strip() for poi in pois if isinstance(poi, dict)]
    categories = [str(poi.get("category", "")).strip() for poi in pois if isinstance(poi, dict)]
    signature = " -> ".join(category for category in categories if category)
    route_design = get_route_design(task["task_id"])
    expected_categories = [
        str(category).strip()
        for category in route_design.get("category_sequence", [])
    ]

    if categories and expected_categories and categories != expected_categories:
        errors.append(
            f"路线 category 顺序必须严格匹配固定 prompt："
            f"expected {' -> '.join(expected_categories)}，actual {signature}"
        )

    if expected_categories and len(pois) != len(expected_categories):
        errors.append(
            f"plan.pois 数量必须匹配固定 prompt，"
            f"expected {len(expected_categories)}，actual {len(pois)}"
        )

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

        if (
            re.match(r"^[\u4e00-\u9fa5]{2,4}(咖啡|书店|甜品|轻食|茶馆|公园)$", name)
            and not has_quality_name_anchor(name)
        ):
            errors.append(f"POI name 过于泛化，缺少街区/人名/楼层等真实锚点：{name}")

    title = str(plan.get("title", "")).strip()
    if title:
        title_bad_tokens = [token for token in FAKE_NAME_TOKENS if token in title]
        if title_bad_tokens:
            errors.append(f"plan.title 有明显 AI 味：{title}，命中 {title_bad_tokens}")

    anchored_count = sum(1 for name in names if has_quality_name_anchor(name))
    required_anchored_count = min(3, len(names))
    if names and anchored_count < required_anchored_count:
        errors.append(
            f"POI name 深圳/生活化锚点不足：{anchored_count}/{len(names)}，"
            f"至少需要 {required_anchored_count} 个带地名、人名、楼层、数字、英文或口语化小店锚点"
        )

    if categories:
        for bad_sequence in OVERUSED_CATEGORY_SEQUENCES:
            if categories[:len(bad_sequence)] == bad_sequence:
                errors.append(f"路线 category 顺序落入高频套路：{signature}")

        recent_signatures = load_recent_route_signatures(exclude_task_id=task["task_id"], limit=20)
        if signature in recent_signatures:
            errors.append(f"路线 category 顺序与已生成路线重复：{signature}")

        if len(categories) >= 4:
            food_or_rest = {"咖啡", "甜品", "轻食", "茶馆", "餐厅"}
            core_experience_categories = {
                "游乐园", "亲子空间", "密室逃脱", "真人CS", "电竞馆", "网吧",
                "KTV", "桌游", "运动", "小剧场", "展览", "手作体验", "Citywalk", "公园"
            }
            passive_count = sum(1 for category in categories if category in food_or_rest)
            has_core_experience = any(category in core_experience_categories for category in categories)
            passive_allowed_scenes = {"family", "friends", "night_gathering", "low_budget", "solo_relax"}
            if (
                passive_count >= len(categories) - 1
                and task["scene_id"] not in passive_allowed_scenes
                and not has_core_experience
            ):
                errors.append(f"路线过度依赖吃喝坐店，缺少核心体验或街区主线：{signature}")

        if task["scene_id"] == "parent_child" and task.get("route_index") in {1, 2}:
            child_core_categories = {"游乐园", "亲子空间"}
            core_stays = [
                int(poi.get("avg_stay_minutes", 0) or 0)
                for poi in pois
                if isinstance(poi, dict) and poi.get("category") in child_core_categories
            ]
            if not core_stays:
                errors.append("亲子半日/雨天路线缺少游乐园或亲子空间作为核心主场")
            elif max(core_stays) < 150:
                errors.append("亲子核心主场停留时间不足，应体现一个游乐园/亲子馆占据大半个下午")

        if task["scene_id"] in {"friends", "night_gathering"}:
            if not any(category in FRIEND_REAL_LIFE_CATEGORIES for category in categories):
                errors.append(
                    "朋友/夜间路线缺少真实生活化朋友局元素：烧烤、火锅、烤肉、桑拿鸡、"
                    "电竞/网吧、密室、真人CS、KTV、桌游或夜间活动"
                )

    return errors


def summarize_plan_for_log(data: Dict[str, Any]) -> str:
    plan = data.get("plan", {})
    names = [str(poi.get("name")) for poi in plan.get("pois", []) if isinstance(poi, dict)]
    signature = route_signature_from_plan(plan)
    return f"title={plan.get('title')} | categories={signature} | names={' | '.join(names)}"


def build_prompt(
    task: Dict[str, Any],
    candidate_points: List[Dict[str, Any]],
    previous_errors: Optional[List[str]] = None
) -> str:
    registry = load_registry()
    used_names = registry.get("used_poi_names", [])
    used_names_sample = used_names[-80:] if len(used_names) > 80 else used_names
    blueprint = get_route_blueprint(task["task_id"])
    scene_reality_guide = get_scene_reality_guide(task["scene_id"])
    route_design = get_route_design(task["task_id"])
    recent_signatures = load_recent_route_signatures(exclude_task_id=task["task_id"])
    previous_errors = previous_errors or []

    return f"""
请为以下任务生成 Local Activity Sandbox 数据。

任务 ID：{task["task_id"]}
场景 ID：{task["scene_id"]}
场景名称：{task["scene_name"]}
目标用户：{task["target_user"]}
路线序号：{task["route_index"]}
路线风格：{task["route_style"]}

本路线必须满足：
{json.dumps(task["must_have"], ensure_ascii=False, indent=2)}

本路线需要避免：
{json.dumps(task["avoid"], ensure_ascii=False, indent=2)}

本路线必须采用的差异化骨架：
{json.dumps(blueprint, ensure_ascii=False, indent=2)}

本路线已经由监督者预先定好，模型不得重新策划路线，只能按以下固定路线设计补全 JSON：
{json.dumps(route_design, ensure_ascii=False, indent=2)}

强制执行规则：
1. plan.pois 数量必须等于 fixed route 的 category_sequence 数量。
2. plan.pois 的顺序必须完全等于 category_sequence。
3. 每个 POI 的 category 必须严格使用对应 slot 的 category。
4. 每个 POI 的 name 必须贴近对应 slot 的 name_hint，可以略微自然化，但不能换成其他风格。
5. 每个 POI 的 avg_stay_minutes、avg_price、description、risk_notes、backup_plans 要体现对应 slot 的 role 和 must_reflect。
6. route_edges 必须按这个固定顺序连接相邻 POI。

结合真实深圳周末生活场景，本场景要参考这些现实约束和玩法：
{json.dumps(scene_reality_guide, ensure_ascii=False, indent=2)}

最近已经生成过的 category 顺序如下。本次不要重复，也不要只做轻微调换：
{json.dumps(recent_signatures, ensure_ascii=False, indent=2)}

上一轮生成被质检驳回的问题如下。本轮必须逐条修正：
{json.dumps(previous_errors[:30], ensure_ascii=False, indent=2)}

可用 source_points 如下。
你必须从这些点中选择 4-5 个作为 POI。
每个 POI 的 source_instance、source_feature、lon、lat 必须与所选 source_point 完全一致。
不要使用 source_points 之外的经纬度。

source_points:
{json.dumps(candidate_points, ensure_ascii=False, indent=2)}

以下 POI 名称已经用过，请不要重复：
{json.dumps(used_names_sample, ensure_ascii=False, indent=2)}

请特别注意：
1. 这次只生成 1 条 plan。
2. 地点组合要有路线节奏：起点进入状态，中段核心体验，后段休息或收尾。不同路线的节奏结构要不同，不要千篇一律。
3. 每个 POI 都要有足够长的 description，说明适合谁、什么时候适合、有什么风险、交通如何。
4. backup_plans 要体现动态重规划，例如下雨、太累、预算降低、临时带宠物、朋友迟到、想拍照、手机没电等。
5. sample_feedback 要体现游后反馈闭环，能更新用户画像和 POI 公共反馈。
6. 数据要有真实决策冲突，不要让所有点都完美。
7. route_edges 必须按 pois 顺序连接相邻地点。
8. POI 名字要像真实深圳店名，自然多样，不要AI味。4-5个名字风格必须各不相同。
9. 生成前先用一句话在心里确定路线骨架，但不要把这句话输出到 JSON 之外。
10. 如果你发现自己想写"悠然/静心/萌芽/欢乐/甜蜜/星空/时光/工坊/小屋/乐园/空间"，立刻换成更像深圳街巷小店的名字。

{SCHEMA_REQUIREMENT}
"""


# ============================================================
# JSON 解析与修复
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
            raise ValueError(f"JSON 解析失败，且未安装 json-repair：{e}")

    try:
        repaired = repair_json(candidate)
        return json.loads(repaired)
    except Exception as e:
        raise ValueError(f"JSON 修复失败：{e}")


def repair_json_with_llm(raw_text: str, error_message: str) -> str:
    repair_prompt = f"""
下面是一段模型生成的 JSON，但它不是合法 JSON。

解析错误：
{error_message}

请你只做 JSON 格式修复：
1. 不要添加解释。
2. 不要使用 Markdown。
3. 不要改变字段含义。
4. 不要删除已有字段。
5. 只返回修复后的完整 JSON 对象。

损坏 JSON 如下：
{raw_text}
"""
    return call_llm(repair_prompt)


# ============================================================
# 校验
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


def is_late_open(open_hours: str) -> bool:
    if not isinstance(open_hours, str) or "-" not in open_hours:
        return False

    end = open_hours.split("-")[-1].strip()

    if end == "24:00":
        return True

    try:
        hour, minute = end.split(":")
        hour_i = int(hour)
        minute_i = int(minute)

        if hour_i <= 5:
            return True

        return hour_i > 22 or (hour_i == 22 and minute_i > 0)
    except Exception:
        return False


def as_float(value: Any, default: float = 0.0) -> float:
    if value is None:
        return default
    try:
        return float(value)
    except Exception:
        return default


def validate_no_global_duplicates(plan: Dict[str, Any]) -> List[str]:
    errors = []

    registry = load_registry()
    used_instances = set(int(x) for x in registry.get("used_source_instances", []))
    used_names = set(str(x) for x in registry.get("used_poi_names", []))

    local_instances = set()
    local_names = set()

    for poi in plan.get("pois", []):
        instance = poi.get("source_instance")
        name = poi.get("name")

        if instance is not None:
            try:
                instance_i = int(instance)
                if instance_i in used_instances:
                    errors.append(f"source_instance 全局重复：{instance_i}")
                if instance_i in local_instances:
                    errors.append(f"source_instance plan 内重复：{instance_i}")
                local_instances.add(instance_i)
            except Exception:
                errors.append(f"source_instance 非法：{instance}")

        if name:
            name_s = str(name)
            if name_s in used_names:
                errors.append(f"POI name 全局重复：{name_s}")
            if name_s in local_names:
                errors.append(f"POI name plan 内重复：{name_s}")
            local_names.add(name_s)

    return errors


def validate_task_data(
    data: Dict[str, Any],
    task: Dict[str, Any],
    candidate_points: List[Dict[str, Any]]
) -> List[str]:
    errors: List[str] = []

    if data.get("task_id") != task["task_id"]:
        errors.append(f"task_id 不匹配，应为 {task['task_id']}，实际为 {data.get('task_id')}")

    if data.get("scene_id") != task["scene_id"]:
        errors.append(f"scene_id 不匹配，应为 {task['scene_id']}，实际为 {data.get('scene_id')}")

    if data.get("scene_name") != task["scene_name"]:
        errors.append(f"scene_name 不匹配，应为 {task['scene_name']}，实际为 {data.get('scene_name')}")

    if data.get("route_index") != task["route_index"]:
        errors.append(f"route_index 不匹配，应为 {task['route_index']}，实际为 {data.get('route_index')}")

    if data.get("route_style") != task["route_style"]:
        errors.append(f"route_style 不匹配，应为 {task['route_style']}，实际为 {data.get('route_style')}")

    plan = data.get("plan")
    if not isinstance(plan, dict):
        errors.append("plan 必须是对象")
        return errors

    required_plan_fields = [
        "plan_id", "title", "route_style", "summary",
        "recommended_start_time", "total_budget", "total_duration_minutes",
        "total_walking_minutes", "weather_fit", "route_tags",
        "suitable_for", "risk_notes", "pois", "route_edges",
        "backup_plans", "sample_feedback"
    ]
    check_required_fields(plan, required_plan_fields, "plan", errors)

    if plan.get("route_style") != task["route_style"]:
        errors.append(f"plan.route_style 不匹配，应为 {task['route_style']}")

    candidate_map = {
        int(p["source_instance"]): p
        for p in candidate_points
    }

    pois = plan.get("pois", [])
    if not isinstance(pois, list):
        errors.append("plan.pois 必须是数组")
        return errors

    if not (4 <= len(pois) <= 5):
        errors.append(f"plan.pois 必须有 4-5 个，实际为 {len(pois)}")

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
                errors.append(f"{prefix}.source_instance 不在本次 candidate_points 中：{instance_i}")
            else:
                source_point = candidate_map[instance_i]
                if str(poi.get("source_feature")) != str(source_point["source_feature"]):
                    errors.append(f"{prefix}.source_feature 与 source_points 不一致")

                lon = poi.get("lon")
                lat = poi.get("lat")

                if abs(float(lon) - float(source_point["lon"])) > 1e-8:
                    errors.append(f"{prefix}.lon 与 source_points 不一致")
                if abs(float(lat) - float(source_point["lat"])) > 1e-8:
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
        else:
            errors.append(f"{prefix}.facilities 必须是对象")
            facilities = {}

        transportation = poi.get("transportation", {})
        if isinstance(transportation, dict):
            check_required_fields(transportation, REQUIRED_TRANSPORTATION_FIELDS, f"{prefix}.transportation", errors)
            subway = transportation.get("subway", {})
            if isinstance(subway, dict):
                check_required_fields(subway, REQUIRED_SUBWAY_FIELDS, f"{prefix}.transportation.subway", errors)
            else:
                errors.append(f"{prefix}.transportation.subway 必须是对象")
        else:
            errors.append(f"{prefix}.transportation 必须是对象")
            transportation = {}

        business_rules = poi.get("business_rules", {})
        if isinstance(business_rules, dict):
            check_required_fields(business_rules, REQUIRED_BUSINESS_RULE_FIELDS, f"{prefix}.business_rules", errors)
        else:
            errors.append(f"{prefix}.business_rules 必须是对象")
            business_rules = {}

        community_feedback = poi.get("community_feedback", {})
        if isinstance(community_feedback, dict):
            check_required_fields(
                community_feedback,
                REQUIRED_COMMUNITY_FEEDBACK_FIELDS,
                f"{prefix}.community_feedback",
                errors
            )
            score_adjustments = community_feedback.get("score_adjustments", {})
            if isinstance(score_adjustments, dict):
                check_required_fields(
                    score_adjustments,
                    REQUIRED_SCORE_ADJUSTMENT_FIELDS,
                    f"{prefix}.community_feedback.score_adjustments",
                    errors
                )
            else:
                errors.append(f"{prefix}.community_feedback.score_adjustments 必须是对象")
        else:
            errors.append(f"{prefix}.community_feedback 必须是对象")

        category = poi.get("category")
        if category in ["公园", "Citywalk"]:
            if poi.get("indoor") is not False:
                errors.append(f"{prefix}: {category} 通常应 indoor=false")
            if business_rules.get("min_spend") not in [0, None]:
                errors.append(f"{prefix}: {category} 的 min_spend 应为 0")
            if facilities.get("air_conditioning") is not False:
                errors.append(f"{prefix}: {category} 的 air_conditioning 应为 false")
            if facilities.get("wifi") is not False:
                errors.append(f"{prefix}: {category} 的 wifi 应为 false")

    edges = plan.get("route_edges", [])
    if not isinstance(edges, list):
        errors.append("plan.route_edges 必须是数组")
    else:
        if len(edges) < max(0, len(pois) - 1):
            errors.append(f"plan.route_edges 数量不足，至少需要 {len(pois) - 1}")

        expected_pairs: List[Tuple[str, str]] = []
        for i in range(len(pois) - 1):
            expected_pairs.append((pois[i].get("id"), pois[i + 1].get("id")))

        actual_pairs = []

        for edge_index, edge in enumerate(edges, start=1):
            prefix = f"plan.route_edges[{edge_index}]"

            if not isinstance(edge, dict):
                errors.append(f"{prefix} 必须是对象")
                continue

            check_required_fields(edge, REQUIRED_EDGE_FIELDS, prefix, errors)

            from_id = edge.get("from")
            to_id = edge.get("to")

            if from_id not in poi_ids:
                errors.append(f"{prefix}.from 引用了不存在的 POI：{from_id}")
            if to_id not in poi_ids:
                errors.append(f"{prefix}.to 引用了不存在的 POI：{to_id}")

            actual_pairs.append((from_id, to_id))

        for pair in expected_pairs:
            if pair not in actual_pairs:
                errors.append(f"plan.route_edges 缺少相邻连接：{pair[0]} -> {pair[1]}")

    backup_plans = plan.get("backup_plans", [])
    if not isinstance(backup_plans, list) or len(backup_plans) < 2:
        errors.append("plan.backup_plans 至少需要 2 条")

    sample_feedback = plan.get("sample_feedback", [])
    if not isinstance(sample_feedback, list) or len(sample_feedback) < 2:
        errors.append("plan.sample_feedback 至少需要 2 条")

    # 全局去重校验
    errors.extend(validate_no_global_duplicates(plan))

    # 质量巡检：避免假店名和重复路线骨架
    errors.extend(validate_plan_quality(plan, task))

    # 场景专项校验
    scene_id = task["scene_id"]

    if scene_id == "rainy_indoor":
        for poi in pois:
            if poi.get("indoor") is not True:
                errors.append(f"雨天室内场景存在 indoor=false 的 POI：{poi.get('id')}")
            if "雨天" not in poi.get("weather_fit", []):
                errors.append(f"雨天室内场景存在 weather_fit 不含雨天的 POI：{poi.get('id')}")

    if scene_id == "low_budget":
        if plan.get("total_budget", 999999) > 120:
            errors.append("低预算路线 total_budget 超过 120")
        if not any(poi.get("avg_price") == 0 for poi in pois):
            errors.append("低预算路线没有免费 POI")

    if scene_id == "pet_friendly":
        pet_count = 0
        for poi in pois:
            facilities = poi.get("facilities", {})
            rules = poi.get("business_rules", {})
            if facilities.get("pet_friendly") or rules.get("pets_allowed_inside"):
                pet_count += 1
        if pet_count < 2:
            errors.append("宠物友好路线 pet_friendly POI 少于 2 个")

    if scene_id == "family":
        if plan.get("total_walking_minutes", 999999) > 40:
            errors.append("家人同行路线 total_walking_minutes 超过 40")
        for poi in pois:
            if poi.get("transportation", {}).get("walking_difficulty") == "high":
                errors.append(f"家人同行路线存在 walking_difficulty=high 的 POI：{poi.get('id')}")

    if scene_id == "photo_checkin":
        if pois:
            avg_photo = sum(as_float(poi.get("photo_score"), 0) for poi in pois) / len(pois)
            if avg_photo < 4.5:
                errors.append(f"拍照打卡路线平均 photo_score 小于 4.5：{avg_photo:.2f}")

    if scene_id == "solo_relax":
        if pois:
            avg_energy = sum(as_float(poi.get("energy_level"), 9) for poi in pois) / len(pois)
            if avg_energy > 1.7:
                errors.append(f"独处放松路线平均 energy_level 大于 1.7：{avg_energy:.2f}")

    if scene_id == "night_gathering":
        late_count = sum(1 for poi in pois if is_late_open(str(poi.get("open_hours", ""))))
        if late_count < 2:
            errors.append("夜间小聚路线营业到 22:00 后的 POI 少于 2 个")

    if scene_id == "parent_child":
        has_child_friendly = False
        for poi in pois:
            facilities = poi.get("facilities", {})
            suitable_for = poi.get("suitable_for", [])
            if (
                facilities.get("restroom")
                or facilities.get("accessible")
                or facilities.get("baby_care_room")
                or "亲子" in suitable_for
            ):
                has_child_friendly = True
        if not has_child_friendly:
            errors.append("亲子路线缺少亲子友好设施或 suitable_for=亲子 的地点")

    if scene_id == "couple_date":
        if pois:
            avg_photo = sum(as_float(poi.get("photo_score"), 0) for poi in pois) / len(pois)
            avg_conv = sum(as_float(poi.get("conversation_score"), 0) for poi in pois) / len(pois)
            if max(avg_photo, avg_conv) < 4.3:
                errors.append("情侣路线平均 photo_score 和 conversation_score 都低于 4.3")

    if scene_id == "friends":
        count = 0
        for poi in pois:
            if as_float(poi.get("conversation_score"), 0) >= 4.2 or "互动" in poi.get("activity_tags", []):
                count += 1
        if count < 2:
            errors.append("朋友聚会路线中高聊天/互动地点少于 2 个")

    return errors


def normalize_task_metadata(data: Dict[str, Any], task: Dict[str, Any]) -> None:
    """
    这些字段由任务配置决定，不让模型的措辞差异触发无意义重试。
    """
    data["task_id"] = task["task_id"]
    data["scene_id"] = task["scene_id"]
    data["scene_name"] = task["scene_name"]
    data["target_user"] = task["target_user"]
    data["route_index"] = task["route_index"]
    data["route_style"] = task["route_style"]

    plan = data.get("plan")
    if isinstance(plan, dict):
        plan["route_style"] = task["route_style"]


# ============================================================
# OpenAI-compatible API
# ============================================================

def call_llm(prompt: str) -> str:
    kwargs: Dict[str, Any] = {
        "model": OPENAI_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.65,
        "max_tokens": MAX_TOKENS
    }

    if USE_JSON_MODE:
        kwargs["response_format"] = {"type": "json_object"}

    response = client.chat.completions.create(**kwargs)
    content = response.choices[0].message.content

    if content is None:
        raise ValueError("模型返回内容为空")

    return content.strip()


# ============================================================
# 单任务生成
# ============================================================

def generate_task(task: Dict[str, Any]) -> Dict[str, Any]:
    task_id = task["task_id"]
    json_path = JSON_DIR / f"{task_id}.json"
    raw_path = RAW_DIR / f"{task_id}.txt"

    if json_path.exists():
        print(f"[SKIP] {task_id} 已存在：{json_path}")
        with json_path.open("r", encoding="utf-8") as f:
            return json.load(f)

    last_error = None
    previous_errors: List[str] = []

    for attempt in range(1, MAX_RETRY_PER_TASK + 2):
        print(f"[CALL] 生成任务：{task_id} / {task['scene_name']} / {task['route_style']}，第 {attempt} 次尝试")

        candidate_points = sample_points_for_task(task_id=f"{task_id}_attempt_{attempt}", count=CANDIDATE_POINTS_PER_TASK)
        prompt = build_prompt(task, candidate_points, previous_errors=previous_errors)

        try:
            raw_text = call_llm(prompt)

            raw_attempt_path = RAW_DIR / f"{task_id}_attempt_{attempt}.txt"
            raw_attempt_path.write_text(raw_text, encoding="utf-8")

            try:
                data = extract_json(raw_text)
            except Exception as parse_error:
                print(f"[WARN] 初次 JSON 解析失败，尝试让模型修复：{parse_error}")
                repaired_text = repair_json_with_llm(raw_text, str(parse_error))
                repaired_path = RAW_DIR / f"{task_id}_attempt_{attempt}_repaired.txt"
                repaired_path.write_text(repaired_text, encoding="utf-8")
                data = extract_json(repaired_text)

            normalize_task_metadata(data, task)
            print(f"[AUDIT] {task_id}: {summarize_plan_for_log(data)}")
            errors = validate_task_data(data, task, candidate_points)
            previous_errors = errors

            data["_meta"] = {
                "task_id": task_id,
                "scene_id": task["scene_id"],
                "scene_name": task["scene_name"],
                "route_index": task["route_index"],
                "route_style": task["route_style"],
                "generated_at": datetime.now().isoformat(timespec="seconds"),
                "attempt": attempt,
                "validation_passed": len(errors) == 0,
                "validation_errors": errors,
                "candidate_source_instances": [p["source_instance"] for p in candidate_points]
            }

            if not errors:
                raw_path.write_text(raw_text, encoding="utf-8")
                json_path.write_text(
                    json.dumps(data, ensure_ascii=False, indent=2),
                    encoding="utf-8"
                )
                update_registry_with_plan(data["plan"])
                print(f"[OK] {task_id} 校验通过，已更新 registry")
                return data

            last_error = f"校验失败：{len(errors)} 个问题"
            print(f"[WARN] {task_id} 校验失败，问题数：{len(errors)}")
            for err in errors[:20]:
                print(f"  - {err}")
            if len(errors) > 20:
                print(f"  ... 还有 {len(errors) - 20} 个问题")

            failed_json_path = JSON_DIR / f"{task_id}_failed_attempt_{attempt}.json"
            failed_json_path.write_text(
                json.dumps(data, ensure_ascii=False, indent=2),
                encoding="utf-8"
            )

        except Exception as e:
            last_error = str(e)
            previous_errors = [f"上一轮生成或解析异常：{last_error}"]
            print(f"[ERROR] {task_id} 第 {attempt} 次生成失败：{e}")

        if attempt <= MAX_RETRY_PER_TASK:
            print(f"[WAIT] 准备重试，等待 {CALL_DELAY_SECONDS} 秒...")
            time.sleep(CALL_DELAY_SECONDS)

    raise RuntimeError(f"{task_id} 生成失败：{last_error}")


# ============================================================
# 合并结果
# ============================================================

def merge_results() -> Dict[str, Any]:
    task_files = sorted(JSON_DIR.glob("*.json"))

    tasks = []
    all_plans = []
    all_pois = []
    all_edges = []
    all_feedback = []
    validation_report = []

    for path in task_files:
        if "_failed_attempt_" in path.name:
            continue

        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        tasks.append(data)

        validation_report.append({
            "file": path.name,
            "task_id": data.get("task_id"),
            "scene_id": data.get("scene_id"),
            "scene_name": data.get("scene_name"),
            "route_index": data.get("route_index"),
            "route_style": data.get("route_style"),
            "validation_passed": data.get("_meta", {}).get("validation_passed"),
            "validation_errors": data.get("_meta", {}).get("validation_errors", [])
        })

        plan = data.get("plan", {})
        if plan:
            all_plans.append({
                "task_id": data.get("task_id"),
                "scene_id": data.get("scene_id"),
                "scene_name": data.get("scene_name"),
                "route_index": data.get("route_index"),
                "route_style": data.get("route_style"),
                **plan
            })

            for poi in plan.get("pois", []):
                all_pois.append({
                    "task_id": data.get("task_id"),
                    "scene_id": data.get("scene_id"),
                    "plan_id": plan.get("plan_id"),
                    **poi
                })

            for edge in plan.get("route_edges", []):
                all_edges.append({
                    "task_id": data.get("task_id"),
                    "scene_id": data.get("scene_id"),
                    "plan_id": plan.get("plan_id"),
                    **edge
                })

            for feedback in plan.get("sample_feedback", []):
                all_feedback.append({
                    "task_id": data.get("task_id"),
                    "scene_id": data.get("scene_id"),
                    "plan_id": plan.get("plan_id"),
                    **feedback
                })

    merged = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "summary": {
            "task_count": len(tasks),
            "plan_count": len(all_plans),
            "poi_count": len(all_pois),
            "route_edge_count": len(all_edges),
            "sample_feedback_count": len(all_feedback)
        },
        "tasks": tasks,
        "plans": all_plans,
        "pois": all_pois,
        "route_edges": all_edges,
        "sample_feedback": all_feedback
    }

    MERGED_FILE.write_text(
        json.dumps(merged, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    VALIDATION_REPORT_FILE.write_text(
        json.dumps(validation_report, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    return merged


# ============================================================
# 主函数
# ============================================================

def run_single_task(task_id: str) -> Optional[Dict[str, Any]]:
    """运行单个任务，用于迭代调试。"""
    rebuild_registry_from_existing_outputs()
    tasks = build_plan_tasks()
    target = None
    for t in tasks:
        if t["task_id"] == task_id:
            target = t
            break
    if target is None:
        print(f"[ERROR] 未找到任务：{task_id}")
        print(f"可用任务：{[t['task_id'] for t in tasks]}")
        return None
    try:
        return generate_task(target)
    except Exception as e:
        print(f"[FAILED] {task_id}：{e}")
        return None


def run_sample_tasks(count: int = 3) -> None:
    """从每个场景各取 1 个任务运行，用于快速测试 prompt 效果。"""
    rebuild_registry_from_existing_outputs()
    tasks = build_plan_tasks()

    # 从每个场景取第 1 个任务
    seen_scenes = set()
    sample_tasks = []
    for t in tasks:
        if t["scene_id"] not in seen_scenes:
            seen_scenes.add(t["scene_id"])
            sample_tasks.append(t)
            if len(sample_tasks) >= count:
                break

    print(f"将运行 {len(sample_tasks)} 个采样任务：")
    for t in sample_tasks:
        print(f"  - {t['task_id']} / {t['scene_name']} / {t['route_style']}")

    for i, task in enumerate(sample_tasks, 1):
        print(f"\n========== [采样 {i}/{len(sample_tasks)}] {task['task_id']} ==========")
        try:
            generate_task(task)
        except Exception as e:
            print(f"[FAILED] {task['task_id']}：{e}")
        if i < len(sample_tasks):
            print(f"[WAIT] 等待 {CALL_DELAY_SECONDS} 秒...")
            time.sleep(CALL_DELAY_SECONDS)


def main() -> None:
    print("========== Local Activity Sandbox 30 Calls 数据生成开始 ==========")
    print(f"模型：{OPENAI_MODEL}")
    print(f"Base URL：{OPENAI_BASE_URL}")
    print(f"JSON Mode：{USE_JSON_MODE}")
    print(f"Max Tokens：{MAX_TOKENS}")
    print(f"每任务候选点数：{CANDIDATE_POINTS_PER_TASK}")
    print(f"输出目录：{OUTPUT_DIR.resolve()}")
    print(f"源点位数量：{len(SOURCE_POINTS)}")
    print("==============================================================")

    # 每次启动时，根据已有成功 JSON 重建 registry，保证断点续跑不重复
    rebuild_registry_from_existing_outputs()

    tasks = build_plan_tasks()
    failed_tasks = []

    for index, task in enumerate(tasks, start=1):
        print(f"\n========== [{index}/{len(tasks)}] {task['task_id']} ==========")

        try:
            generate_task(task)
        except Exception as e:
            failed_tasks.append({
                "task_id": task["task_id"],
                "scene_id": task["scene_id"],
                "scene_name": task["scene_name"],
                "route_index": task["route_index"],
                "route_style": task["route_style"],
                "error": str(e)
            })
            print(f"[FAILED] {task['task_id']} 最终失败：{e}")

        if index < len(tasks):
            print(f"[WAIT] 等待 {CALL_DELAY_SECONDS} 秒后进入下一个任务...")
            time.sleep(CALL_DELAY_SECONDS)

    merged = merge_results()

    print("\n========== 生成完成 ==========")
    print(f"任务数：{merged['summary']['task_count']}")
    print(f"路线数：{merged['summary']['plan_count']}")
    print(f"POI 数：{merged['summary']['poi_count']}")
    print(f"路线边数：{merged['summary']['route_edge_count']}")
    print(f"反馈样例数：{merged['summary']['sample_feedback_count']}")
    print(f"合并文件：{MERGED_FILE}")
    print(f"校验报告：{VALIDATION_REPORT_FILE}")
    print(f"去重注册表：{REGISTRY_FILE}")

    if failed_tasks:
        FAILED_TASKS_FILE.write_text(
            json.dumps(failed_tasks, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        print(f"[WARN] 有失败任务，详情见：{FAILED_TASKS_FILE}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Local Activity Sandbox 数据生成")
    parser.add_argument("--task", type=str, help="只运行指定 task_id")
    parser.add_argument("--sample", type=int, help="从每个场景各取1个任务运行，指定数量")
    parser.add_argument("--clean", action="store_true", help="清理已有输出后运行")
    args = parser.parse_args()

    if args.clean:
        import shutil
        for d in [RAW_DIR, JSON_DIR, LOG_DIR]:
            if d.exists():
                shutil.rmtree(d)
                d.mkdir(parents=True, exist_ok=True)
        if REGISTRY_FILE.exists():
            REGISTRY_FILE.unlink()
        print("[CLEAN] 已清理所有输出文件")

    if args.task:
        run_single_task(args.task)
    elif args.sample:
        run_sample_tasks(args.sample)
    else:
        main()
