import csv
import random
import math
import json
import os
from pathlib import Path

random.seed(42)

SCRIPT_DIR = Path(__file__).resolve().parent
INPUT_FILE = SCRIPT_DIR / "Shenzhen.csv"
OUTPUT_DIR = SCRIPT_DIR / "generated_data"
OUTPUT_DIR.mkdir(exist_ok=True)

NEIGHBOR_COUNT = 6
GRID_CELL_METERS = 1200
SAMPLE_SIZE = 500

SUBWAY_OPTIONS_BY_AREA = {
    "科技生活区": [
        {"station": "高新园", "lines": ["1号线"]},
        {"station": "深大", "lines": ["1号线"]},
        {"station": "粤海门", "lines": ["9号线"]},
        {"station": "后海", "lines": ["2号线", "11号线"]},
    ],
    "海岸漫游区": [
        {"station": "深圳湾公园", "lines": ["9号线"]},
        {"station": "海上世界", "lines": ["2号线", "12号线"]},
        {"station": "湾厦", "lines": ["2号线"]},
        {"station": "红树湾南", "lines": ["9号线", "11号线"]},
    ],
    "艺术仓库区": [
        {"station": "华侨城", "lines": ["1号线"]},
        {"station": "侨城东", "lines": ["1号线"]},
        {"station": "侨城北", "lines": ["2号线"]},
        {"station": "侨香", "lines": ["2号线"]},
    ],
    "商圈活力区": [
        {"station": "购物公园", "lines": ["1号线", "3号线"]},
        {"station": "会展中心", "lines": ["1号线", "4号线"]},
        {"station": "福田", "lines": ["2号线", "3号线", "11号线"]},
        {"station": "岗厦北", "lines": ["2号线", "10号线", "11号线", "14号线"]},
    ],
    "安静生活区": [
        {"station": "宝体", "lines": ["1号线"]},
        {"station": "灵芝", "lines": ["5号线", "12号线"]},
        {"station": "洪浪北", "lines": ["5号线"]},
        {"station": "西乡", "lines": ["1号线"]},
    ],
}

FEATURE_CATEGORY_MAP = {
    "A": "咖啡",
    "B": "书店",
    "C": "甜品",
    "D": "轻食",
    "E": "茶馆",
    "F": "展览",
    "G": "手作体验",
    "H": "小剧场",
    "I": "桌游",
    "J": "公园",
    "K": "Citywalk",
    "L": "买手店",
    "M": "运动",
}

CATEGORY_WEIGHTS = {
    "咖啡": 0.14,
    "书店": 0.08,
    "甜品": 0.08,
    "轻食": 0.10,
    "茶馆": 0.07,
    "展览": 0.10,
    "手作体验": 0.08,
    "小剧场": 0.05,
    "桌游": 0.06,
    "公园": 0.08,
    "Citywalk": 0.08,
    "买手店": 0.05,
    "运动": 0.02,
    "亲子空间": 0.01
}

CATEGORY_TEMPLATES = {
    "咖啡": {
        "price": (35, 70),
        "stay": (45, 90),
        "open_hours": ["09:30-22:30", "10:00-22:00", "10:00-23:00"],
        "indoor_prob": 0.95,
        "energy": [1, 1, 1, 2],
        "mood_tags": ["松弛", "安静", "治愈", "文艺", "适合聊天", "轻办公"],
        "activity_tags": ["聊天", "读书", "休息", "轻办公"],
        "suitable_for": ["独处", "朋友", "约会"],
        "weather_fit": ["晴天", "雨天", "高温"],
        "facility_probs": {
            "restroom": 0.85,
            "pet_friendly": 0.20,
            "charging_available": 0.70,
            "wifi": 0.80,
            "accessible": 0.55,
            "baby_care_room": 0.05,
            "luggage_storage": 0.15,
            "air_conditioning": 0.95
        },
        "rule_probs": {
            "photo_allowed": 0.92,
            "outside_food_allowed": 0.08,
            "group_buy_available": 0.50,
            "reservation_required": 0.12,
            "takeaway_allowed": 0.75,
            "refund_friendly": 0.50
        }
    },
    "书店": {
        "price": (20, 60),
        "stay": (35, 80),
        "open_hours": ["10:00-21:30", "10:30-22:00", "11:00-21:00"],
        "indoor_prob": 1.0,
        "energy": [1, 1, 2],
        "mood_tags": ["安静", "文艺", "治愈", "低刺激", "松弛"],
        "activity_tags": ["读书", "逛店", "拍照", "休息"],
        "suitable_for": ["独处", "朋友", "约会"],
        "weather_fit": ["晴天", "雨天", "高温"],
        "facility_probs": {
            "restroom": 0.55,
            "pet_friendly": 0.10,
            "charging_available": 0.35,
            "wifi": 0.45,
            "accessible": 0.50,
            "baby_care_room": 0.05,
            "luggage_storage": 0.10,
            "air_conditioning": 0.95
        },
        "rule_probs": {
            "photo_allowed": 0.75,
            "outside_food_allowed": 0.05,
            "group_buy_available": 0.20,
            "reservation_required": 0.05,
            "takeaway_allowed": 0.20,
            "refund_friendly": 0.45
        }
    },
    "甜品": {
        "price": (30, 65),
        "stay": (35, 60),
        "open_hours": ["11:00-22:00", "10:30-22:30", "12:00-23:00"],
        "indoor_prob": 0.95,
        "energy": [1, 1, 2],
        "mood_tags": ["可爱", "轻松", "拍照", "治愈"],
        "activity_tags": ["拍照", "聊天", "补充能量"],
        "suitable_for": ["朋友", "约会", "亲子"],
        "weather_fit": ["晴天", "雨天", "高温"],
        "facility_probs": {
            "restroom": 0.65,
            "pet_friendly": 0.18,
            "charging_available": 0.35,
            "wifi": 0.45,
            "accessible": 0.50,
            "baby_care_room": 0.10,
            "luggage_storage": 0.10,
            "air_conditioning": 0.95
        },
        "rule_probs": {
            "photo_allowed": 0.95,
            "outside_food_allowed": 0.05,
            "group_buy_available": 0.55,
            "reservation_required": 0.08,
            "takeaway_allowed": 0.85,
            "refund_friendly": 0.45
        }
    },
    "轻食": {
        "price": (45, 90),
        "stay": (45, 75),
        "open_hours": ["10:30-20:30", "11:00-21:00"],
        "indoor_prob": 0.95,
        "energy": [1, 1, 2],
        "mood_tags": ["健康", "轻松", "清爽", "安静"],
        "activity_tags": ["吃饭", "聊天", "休息"],
        "suitable_for": ["独处", "朋友", "约会"],
        "weather_fit": ["晴天", "雨天", "高温"],
        "facility_probs": {
            "restroom": 0.85,
            "pet_friendly": 0.15,
            "charging_available": 0.30,
            "wifi": 0.55,
            "accessible": 0.55,
            "baby_care_room": 0.10,
            "luggage_storage": 0.10,
            "air_conditioning": 0.95
        },
        "rule_probs": {
            "photo_allowed": 0.85,
            "outside_food_allowed": 0.05,
            "group_buy_available": 0.50,
            "reservation_required": 0.10,
            "takeaway_allowed": 0.85,
            "refund_friendly": 0.45
        }
    },
    "茶馆": {
        "price": (55, 120),
        "stay": (60, 110),
        "open_hours": ["12:00-23:00", "11:00-22:30"],
        "indoor_prob": 1.0,
        "energy": [1, 1, 1],
        "mood_tags": ["安静", "松弛", "聊天", "治愈", "东方美学"],
        "activity_tags": ["聊天", "休息", "品茶"],
        "suitable_for": ["朋友", "约会", "独处"],
        "weather_fit": ["晴天", "雨天", "高温"],
        "facility_probs": {
            "restroom": 0.90,
            "pet_friendly": 0.10,
            "charging_available": 0.40,
            "wifi": 0.50,
            "accessible": 0.45,
            "baby_care_room": 0.05,
            "luggage_storage": 0.15,
            "air_conditioning": 0.95
        },
        "rule_probs": {
            "photo_allowed": 0.80,
            "outside_food_allowed": 0.03,
            "group_buy_available": 0.35,
            "reservation_required": 0.30,
            "takeaway_allowed": 0.30,
            "refund_friendly": 0.40
        }
    },
    "展览": {
        "price": (40, 120),
        "stay": (60, 120),
        "open_hours": ["10:00-18:00", "10:00-19:00"],
        "indoor_prob": 1.0,
        "energy": [1, 2, 2],
        "mood_tags": ["文艺", "拍照", "灵感", "小众", "沉浸"],
        "activity_tags": ["看展", "拍照", "学习", "约会"],
        "suitable_for": ["独处", "朋友", "约会"],
        "weather_fit": ["晴天", "雨天", "高温"],
        "facility_probs": {
            "restroom": 0.90,
            "pet_friendly": 0.05,
            "charging_available": 0.20,
            "wifi": 0.35,
            "accessible": 0.80,
            "baby_care_room": 0.25,
            "luggage_storage": 0.40,
            "air_conditioning": 0.95
        },
        "rule_probs": {
            "photo_allowed": 0.70,
            "outside_food_allowed": 0.02,
            "group_buy_available": 0.35,
            "reservation_required": 0.35,
            "takeaway_allowed": 0.05,
            "refund_friendly": 0.55
        }
    },
    "手作体验": {
        "price": (80, 180),
        "stay": (90, 150),
        "open_hours": ["13:00-21:00", "12:00-21:30"],
        "indoor_prob": 1.0,
        "energy": [2, 2, 3],
        "mood_tags": ["治愈", "互动", "创意", "慢节奏"],
        "activity_tags": ["手作", "互动", "体验", "拍照"],
        "suitable_for": ["朋友", "约会", "亲子"],
        "weather_fit": ["晴天", "雨天", "高温"],
        "facility_probs": {
            "restroom": 0.80,
            "pet_friendly": 0.08,
            "charging_available": 0.30,
            "wifi": 0.40,
            "accessible": 0.45,
            "baby_care_room": 0.15,
            "luggage_storage": 0.15,
            "air_conditioning": 0.95
        },
        "rule_probs": {
            "photo_allowed": 0.90,
            "outside_food_allowed": 0.05,
            "group_buy_available": 0.45,
            "reservation_required": 0.75,
            "takeaway_allowed": 0.05,
            "refund_friendly": 0.45
        }
    },
    "小剧场": {
        "price": (80, 200),
        "stay": (90, 150),
        "open_hours": ["14:00-22:00", "15:00-23:00"],
        "indoor_prob": 1.0,
        "energy": [2, 2],
        "mood_tags": ["沉浸", "文艺", "新鲜", "约会"],
        "activity_tags": ["演出", "观看", "沉浸体验"],
        "suitable_for": ["朋友", "约会"],
        "weather_fit": ["晴天", "雨天", "高温"],
        "facility_probs": {
            "restroom": 0.95,
            "pet_friendly": 0.02,
            "charging_available": 0.15,
            "wifi": 0.25,
            "accessible": 0.65,
            "baby_care_room": 0.10,
            "luggage_storage": 0.25,
            "air_conditioning": 0.95
        },
        "rule_probs": {
            "photo_allowed": 0.35,
            "outside_food_allowed": 0.02,
            "group_buy_available": 0.30,
            "reservation_required": 0.85,
            "takeaway_allowed": 0.02,
            "refund_friendly": 0.35
        }
    },
    "桌游": {
        "price": (55, 120),
        "stay": (120, 180),
        "open_hours": ["13:00-02:00", "12:00-01:00"],
        "indoor_prob": 1.0,
        "energy": [2, 3, 3],
        "mood_tags": ["热闹", "社交", "互动", "夜间"],
        "activity_tags": ["桌游", "社交", "聊天", "多人"],
        "suitable_for": ["朋友", "多人"],
        "weather_fit": ["晴天", "雨天", "高温"],
        "facility_probs": {
            "restroom": 0.90,
            "pet_friendly": 0.08,
            "charging_available": 0.55,
            "wifi": 0.65,
            "accessible": 0.35,
            "baby_care_room": 0.02,
            "luggage_storage": 0.10,
            "air_conditioning": 0.95
        },
        "rule_probs": {
            "photo_allowed": 0.80,
            "outside_food_allowed": 0.10,
            "group_buy_available": 0.45,
            "reservation_required": 0.65,
            "takeaway_allowed": 0.15,
            "refund_friendly": 0.40
        }
    },
    "公园": {
        "price": (0, 0),
        "stay": (40, 100),
        "open_hours": ["06:00-22:00", "00:00-24:00"],
        "indoor_prob": 0.0,
        "energy": [1, 2, 2],
        "mood_tags": ["自然", "散步", "松弛", "低成本", "拍照"],
        "activity_tags": ["散步", "拍照", "休息"],
        "suitable_for": ["独处", "朋友", "约会", "亲子", "宠物"],
        "weather_fit": ["晴天", "阴天"],
        "facility_probs": {
            "restroom": 0.70,
            "pet_friendly": 0.85,
            "charging_available": 0.05,
            "wifi": 0.05,
            "accessible": 0.75,
            "baby_care_room": 0.20,
            "luggage_storage": 0.05,
            "air_conditioning": 0.0
        },
        "rule_probs": {
            "photo_allowed": 0.98,
            "outside_food_allowed": 0.90,
            "group_buy_available": 0.0,
            "reservation_required": 0.0,
            "takeaway_allowed": 0.20,
            "refund_friendly": 0.0
        }
    },
    "Citywalk": {
        "price": (0, 30),
        "stay": (40, 90),
        "open_hours": ["00:00-24:00", "06:00-23:00"],
        "indoor_prob": 0.0,
        "energy": [1, 2, 2],
        "mood_tags": ["城市漫游", "小众", "拍照", "松弛", "探索"],
        "activity_tags": ["散步", "拍照", "逛街"],
        "suitable_for": ["独处", "朋友", "约会"],
        "weather_fit": ["晴天", "阴天"],
        "facility_probs": {
            "restroom": 0.35,
            "pet_friendly": 0.75,
            "charging_available": 0.02,
            "wifi": 0.02,
            "accessible": 0.55,
            "baby_care_room": 0.05,
            "luggage_storage": 0.02,
            "air_conditioning": 0.0
        },
        "rule_probs": {
            "photo_allowed": 0.98,
            "outside_food_allowed": 0.85,
            "group_buy_available": 0.0,
            "reservation_required": 0.0,
            "takeaway_allowed": 0.0,
            "refund_friendly": 0.0
        }
    },
    "买手店": {
        "price": (50, 160),
        "stay": (30, 60),
        "open_hours": ["11:00-21:00", "12:00-22:00"],
        "indoor_prob": 1.0,
        "energy": [1, 2],
        "mood_tags": ["小众", "复古", "潮流", "探索", "拍照"],
        "activity_tags": ["逛店", "购物", "拍照"],
        "suitable_for": ["独处", "朋友", "约会"],
        "weather_fit": ["晴天", "雨天", "高温"],
        "facility_probs": {
            "restroom": 0.35,
            "pet_friendly": 0.15,
            "charging_available": 0.10,
            "wifi": 0.15,
            "accessible": 0.40,
            "baby_care_room": 0.02,
            "luggage_storage": 0.08,
            "air_conditioning": 0.95
        },
        "rule_probs": {
            "photo_allowed": 0.65,
            "outside_food_allowed": 0.03,
            "group_buy_available": 0.25,
            "reservation_required": 0.05,
            "takeaway_allowed": 0.0,
            "refund_friendly": 0.60
        }
    },
    "运动": {
        "price": (60, 160),
        "stay": (60, 120),
        "open_hours": ["09:00-22:00", "10:00-23:00"],
        "indoor_prob": 0.75,
        "energy": [3, 3],
        "mood_tags": ["活力", "释放压力", "社交"],
        "activity_tags": ["运动", "出汗", "体验"],
        "suitable_for": ["朋友", "独处"],
        "weather_fit": ["晴天", "雨天", "高温"],
        "facility_probs": {
            "restroom": 0.95,
            "pet_friendly": 0.05,
            "charging_available": 0.30,
            "wifi": 0.40,
            "accessible": 0.55,
            "baby_care_room": 0.05,
            "luggage_storage": 0.55,
            "air_conditioning": 0.80
        },
        "rule_probs": {
            "photo_allowed": 0.60,
            "outside_food_allowed": 0.05,
            "group_buy_available": 0.35,
            "reservation_required": 0.55,
            "takeaway_allowed": 0.0,
            "refund_friendly": 0.45
        }
    },
    "亲子空间": {
        "price": (80, 180),
        "stay": (90, 150),
        "open_hours": ["10:00-20:00", "09:30-21:00"],
        "indoor_prob": 1.0,
        "energy": [2, 2],
        "mood_tags": ["亲子", "安全", "互动", "轻松"],
        "activity_tags": ["亲子", "体验", "玩乐"],
        "suitable_for": ["亲子"],
        "weather_fit": ["晴天", "雨天", "高温"],
        "facility_probs": {
            "restroom": 0.95,
            "pet_friendly": 0.02,
            "charging_available": 0.40,
            "wifi": 0.50,
            "accessible": 0.80,
            "baby_care_room": 0.80,
            "luggage_storage": 0.35,
            "air_conditioning": 0.95
        },
        "rule_probs": {
            "photo_allowed": 0.75,
            "outside_food_allowed": 0.20,
            "group_buy_available": 0.45,
            "reservation_required": 0.45,
            "takeaway_allowed": 0.05,
            "refund_friendly": 0.55
        }
    }
}

AREA_NAMES = ["科技生活区", "海岸漫游区", "艺术仓库区", "商圈活力区", "安静生活区"]

NAME_PREFIX = {
    "咖啡": ["慢半拍", "午后", "白噪音", "云边", "小岛"],
    "书店": ["纸页之间", "转角", "灯下", "浮光", "句读"],
    "甜品": ["柠檬气泡", "糖纸", "奶油星球", "微甜", "橘子海"],
    "轻食": ["梧桐", "一碗绿", "轻盈", "谷物日记", "晴食"],
    "茶馆": ["黄昏露台", "半盏", "山月", "清风", "一隅"],
    "展览": ["城市切片", "白盒子", "回声", "光影", "海风"],
    "手作体验": ["小满", "慢工", "手心", "陶然", "拾光"],
    "小剧场": ["风铃", "黑匣子", "微光", "即兴", "月台"],
    "桌游": ["夜光", "第六回合", "好友局", "骰子", "不打烊"],
    "公园": ["绿阶", "海岸", "云丘", "荔风", "晴湾"],
    "Citywalk": ["猫步", "梧桐", "旧巷", "转角", "海风"],
    "买手店": ["复古唱片角", "蓝格子", "无名小店", "白日梦", "衣橱"],
    "运动": ["轻汗", "跃动", "风速", "晨练", "能量"],
    "亲子空间": ["小星球", "积木森林", "童梦", "软糖", "彩虹"]
}

NAME_SUFFIX = {
    "咖啡": ["咖啡", "咖啡馆", "Coffee"],
    "书店": ["书店", "书房", "阅读空间"],
    "甜品": ["甜品店", "甜品屋", "Dessert"],
    "轻食": ["轻食社", "轻食餐厅", "沙拉店"],
    "茶馆": ["茶馆", "茶室", "茶空间"],
    "展览": ["展厅", "艺术空间", "Gallery"],
    "手作体验": ["手作坊", "手作空间", "体验馆"],
    "小剧场": ["小剧场", "剧场", "黑盒剧场"],
    "桌游": ["桌游局", "桌游馆", "Boardgame"],
    "公园": ["小公园", "公园", "绿地"],
    "Citywalk": ["小巷", "街区", "步行线"],
    "买手店": ["买手店", "杂货铺", "生活馆"],
    "运动": ["运动馆", "轻运动空间", "球馆"],
    "亲子空间": ["亲子乐园", "亲子空间", "儿童活动馆"]
}

def choose_weighted(weight_dict):
    items = list(weight_dict.keys())
    weights = list(weight_dict.values())
    return random.choices(items, weights=weights, k=1)[0]

def normalize_feature(value):
    return str(value or "").strip().upper()

def parse_instance(value, fallback):
    try:
        return int(float(str(value).strip()))
    except (TypeError, ValueError):
        return fallback

def read_input_rows(input_file):
    required_columns = {"Feature", "Instance", "Lon", "Lat"}
    rows = []

    with Path(input_file).open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        missing_columns = required_columns - set(reader.fieldnames or [])
        if missing_columns:
            missing = ", ".join(sorted(missing_columns))
            raise ValueError(f"{input_file} 缺少必要列: {missing}")

        for line_no, row in enumerate(reader, start=2):
            try:
                lon = float(str(row["Lon"]).strip())
                lat = float(str(row["Lat"]).strip())
            except (TypeError, ValueError):
                continue

            feature = normalize_feature(row.get("Feature"))
            rows.append({
                "Feature": feature,
                "Instance": parse_instance(row.get("Instance"), len(rows) + 1),
                "Lon": lon,
                "Lat": lat,
                "source_line": line_no,
            })

    if not rows:
        raise ValueError(f"{input_file} 没有可用的经纬度数据")

    return rows

def get_sample_size():
    raw_value = os.environ.get("SAMPLE_SIZE", SAMPLE_SIZE)
    try:
        sample_size = int(raw_value)
    except (TypeError, ValueError):
        raise ValueError(f"SAMPLE_SIZE 必须是整数，当前值为: {raw_value}")

    if sample_size <= 0:
        raise ValueError("SAMPLE_SIZE 必须大于 0")

    return sample_size

def chance(p):
    return random.random() < p

def pick_some(items, min_n=2, max_n=4):
    n = random.randint(min_n, min(max_n, len(items)))
    return random.sample(items, n)

def haversine_meters(lon1, lat1, lon2, lat2):
    r = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))

def assign_area(lon, lat, lon_min, lon_max, lat_min, lat_max):
    lon_ratio = (lon - lon_min) / max(lon_max - lon_min, 1e-9)
    lat_ratio = (lat - lat_min) / max(lat_max - lat_min, 1e-9)

    if lat_ratio > 0.66:
        return "海岸漫游区"
    if lon_ratio < 0.33:
        return "安静生活区"
    if lon_ratio > 0.66:
        return "商圈活力区"
    if lat_ratio < 0.33:
        return "艺术仓库区"
    return "科技生活区"

def generate_name(category):
    return random.choice(NAME_PREFIX[category]) + random.choice(NAME_SUFFIX[category])

def generate_subway_info(area):
    station_info = random.choice(SUBWAY_OPTIONS_BY_AREA[area])
    walk_minutes = random.randint(4, 18)
    distance_meters = walk_minutes * random.randint(70, 95)
    exit_name = random.choice(["A", "B", "C", "D", "E"])

    return {
        "nearest_station": station_info["station"],
        "lines": station_info["lines"],
        "exit": f"{exit_name}口",
        "distance_meters": distance_meters,
        "walk_minutes": walk_minutes,
        "recommended": distance_meters <= 900,
        "last_train_buffer_minutes": random.randint(30, 90),
        "access_note": f"从{station_info['station']}站{exit_name}口出站，步行约{walk_minutes}分钟可到达。"
    }

def generate_description(name, category, area, avg_price, avg_stay, open_hours, indoor, mood_tags, activity_tags, suitable_for, transportation, facilities, crowd_risk, queue_risk):
    subway = transportation["subway"]
    weather_tip = "室内空调比较友好，雨天或高温天也适合安排。" if indoor else "户外感更强，晴天和阴天会更舒服，雨天建议谨慎安排。"
    crowd_tip = {
        "low": "整体节奏比较轻，通常不用把时间卡得太紧。",
        "medium": "周末可能会有一些人流，建议预留一点排队和找座时间。",
        "high": "热门时段人会偏多，更适合提前规划到达时间。"
    }[crowd_risk]
    queue_tip = {
        "low": "排队压力不大，适合作为路线中的轻松节点。",
        "medium": "可能需要短暂等待，适合搭配附近点位一起安排。",
        "high": "高峰时段可能排队，赶时间时可以放在备选方案里。"
    }[queue_risk]
    facility_bits = []
    if facilities["wifi"]:
        facility_bits.append("有 Wi-Fi")
    if facilities["charging_available"]:
        facility_bits.append("方便充电")
    if facilities["pet_friendly"]:
        facility_bits.append("对宠物较友好")
    if facilities["accessible"]:
        facility_bits.append("无障碍友好度不错")
    facility_text = "，".join(facility_bits) if facility_bits else "基础设施偏简洁"

    return (
        f"{name}位于深圳{area}，是一个偏{random.choice(mood_tags)}的{category}点位，"
        f"适合{random.choice(suitable_for)}在周末安排{random.choice(activity_tags)}。"
        f"这里人均约{avg_price}元，建议停留{avg_stay}分钟左右，营业时间通常为{open_hours}。"
        f"{weather_tip}{crowd_tip}{queue_tip}"
        f"交通上，最近的地铁站是{subway['nearest_station']}站，"
        f"可乘坐{'、'.join(subway['lines'])}，从{subway['exit']}出站后步行约{subway['walk_minutes']}分钟。"
        f"现场{facility_text}，更适合放进一条轻量、不赶路的城市周末路线里。"
    )

def generate_poi(row, index, bounds):
    lon = float(row["Lon"])
    lat = float(row["Lat"])
    feature = normalize_feature(row.get("Feature"))
    category = FEATURE_CATEGORY_MAP.get(feature, choose_weighted(CATEGORY_WEIGHTS))
    t = CATEGORY_TEMPLATES[category]

    area = assign_area(lon, lat, *bounds)
    name = generate_name(category)
    avg_price = random.randint(*t["price"])
    avg_stay = random.randint(*t["stay"])
    open_hours = random.choice(t["open_hours"])
    indoor = chance(t["indoor_prob"])
    energy_level = random.choice(t["energy"])
    crowd_risk = random.choices(["low", "medium", "high"], weights=[0.35, 0.45, 0.20])[0]
    queue_risk = random.choices(["low", "medium", "high"], weights=[0.45, 0.40, 0.15])[0]
    mood_tags = pick_some(t["mood_tags"], 3, 5)
    activity_tags = pick_some(t["activity_tags"], 2, 4)
    suitable_for = pick_some(t["suitable_for"], 1, min(3, len(t["suitable_for"])))

    facilities = {k: chance(v) for k, v in t["facility_probs"].items()}
    facilities["seating_quality"] = random.choice(["normal", "good", "excellent"])
    if not indoor:
        facilities["air_conditioning"] = False
        facilities["charging_available"] = False
        facilities["wifi"] = False

    subway = generate_subway_info(area)
    transportation = {
        "subway": subway,
        "subway_station": subway["nearest_station"],
        "subway_lines": subway["lines"],
        "subway_exit": subway["exit"],
        "subway_distance_meters": subway["distance_meters"],
        "subway_walk_minutes": subway["walk_minutes"],
        "bus_distance_meters": random.randint(80, 800),
        "parking_available": chance(0.35 if area in ["商圈活力区", "科技生活区"] else 0.55),
        "parking_fee": None,
        "bike_parking_available": chance(0.75),
        "taxi_dropoff_friendly": chance(0.65),
        "walking_difficulty": random.choices(["low", "medium", "high"], weights=[0.65, 0.28, 0.07])[0]
    }
    if transportation["parking_available"]:
        transportation["parking_fee"] = random.choice(["免费", "5元/小时", "10元/小时", "15元/小时"])

    business_rules = {k: chance(v) for k, v in t["rule_probs"].items()}
    business_rules["min_spend"] = random.choice([0, 0, 0, 30, 50, 80]) if category in ["茶馆", "小剧场", "桌游"] else random.choice([0, 0, 0, 20])
    business_rules["time_limit_minutes"] = random.choice([None, 90, 120, 150]) if category in ["咖啡", "茶馆", "桌游"] else None
    business_rules["age_restriction"] = "18+" if category == "桌游" and chance(0.15) else None
    business_rules["dress_code"] = None
    business_rules["quiet_required"] = category in ["书店", "展览"] and chance(0.5)
    business_rules["pets_allowed_inside"] = facilities["pet_friendly"] and indoor

    photo_score = round(random.uniform(3.2, 4.9), 1)
    conversation_score = round(random.uniform(3.2, 4.9), 1)
    novelty_score = round(random.uniform(3.1, 4.9), 1)
    relax_score = round(random.uniform(3.2, 4.9), 1)

    # 类别修正，让分数更合理
    if category in ["展览", "Citywalk", "甜品", "买手店"]:
        photo_score = round(min(5.0, photo_score + 0.4), 1)
    if category in ["咖啡", "茶馆", "轻食"]:
        conversation_score = round(min(5.0, conversation_score + 0.3), 1)
        relax_score = round(min(5.0, relax_score + 0.4), 1)
    if category in ["手作体验", "小剧场", "桌游"]:
        novelty_score = round(min(5.0, novelty_score + 0.5), 1)
    if category in ["桌游", "运动"]:
        relax_score = round(max(2.5, relax_score - 0.5), 1)

    poi = {
        "id": f"sz_poi_{index:03d}",
        "source_instance": int(row.get("Instance", index)),
        "source_feature": feature,
        "name": name,
        "category": category,
        "city": "深圳",
        "area": area,
        "lon": lon,
        "lat": lat,
        "address": f"深圳市{area}虚拟街区 {random.randint(1, 99)} 号",

        "avg_price": avg_price,
        "open_hours": open_hours,
        "avg_stay_minutes": avg_stay,
        "reservation_required": business_rules["reservation_required"],

        "indoor": indoor,
        "weather_fit": t["weather_fit"],
        "energy_level": energy_level,
        "crowd_risk": crowd_risk,
        "queue_risk": queue_risk,

        "mood_tags": mood_tags,
        "activity_tags": activity_tags,
        "suitable_for": suitable_for,
        "avoid_for": [],

        "photo_score": photo_score,
        "conversation_score": conversation_score,
        "novelty_score": novelty_score,
        "relax_score": relax_score,

        "facilities": facilities,
        "transportation": transportation,
        "business_rules": business_rules,

        "community_feedback": {
            "feedback_count": random.randint(0, 35),
            "positive_rate": round(random.uniform(0.65, 0.95), 2),
            "common_praises": [],
            "common_issues": [],
            "tag_votes": {},
            "score_adjustments": {
                "photo_score": 0.0,
                "conversation_score": 0.0,
                "novelty_score": 0.0,
                "relax_score": 0.0
            }
        },

        "description": generate_description(
            name,
            category,
            area,
            avg_price,
            avg_stay,
            open_hours,
            indoor,
            mood_tags,
            activity_tags,
            suitable_for,
            transportation,
            facilities,
            crowd_risk,
            queue_risk
        )
    }

    return poi

def lon_lat_to_xy_meters(lon, lat, origin_lon, origin_lat):
    meters_per_degree_lat = 110_540
    meters_per_degree_lon = 111_320 * math.cos(math.radians(origin_lat))
    return (
        (lon - origin_lon) * meters_per_degree_lon,
        (lat - origin_lat) * meters_per_degree_lat,
    )

def generate_edges(pois, k=NEIGHBOR_COUNT, cell_meters=GRID_CELL_METERS):
    if len(pois) <= 1:
        return []

    origin_lon = min(p["lon"] for p in pois)
    origin_lat = min(p["lat"] for p in pois)
    grid = {}

    for poi in pois:
        x, y = lon_lat_to_xy_meters(poi["lon"], poi["lat"], origin_lon, origin_lat)
        cell = (math.floor(x / cell_meters), math.floor(y / cell_meters))
        poi["_grid_cell"] = cell
        grid.setdefault(cell, []).append(poi)

    min_cell_x = min(cell[0] for cell in grid)
    max_cell_x = max(cell[0] for cell in grid)
    min_cell_y = min(cell[1] for cell in grid)
    max_cell_y = max(cell[1] for cell in grid)
    max_radius = max(max_cell_x - min_cell_x, max_cell_y - min_cell_y) + 1
    min_candidate_count = max(k * 4, 24)

    edges = []
    for p in pois:
        candidates = []
        seen_ids = set()
        cell_x, cell_y = p["_grid_cell"]

        for radius in range(max_radius + 1):
            for dx in range(-radius, radius + 1):
                for dy in range(-radius, radius + 1):
                    if max(abs(dx), abs(dy)) != radius:
                        continue

                    for q in grid.get((cell_x + dx, cell_y + dy), []):
                        if p["id"] == q["id"] or q["id"] in seen_ids:
                            continue
                        seen_ids.add(q["id"])
                        d = haversine_meters(p["lon"], p["lat"], q["lon"], q["lat"])
                        candidates.append((q, d))

            if radius >= 1 and len(candidates) >= min_candidate_count:
                break

        candidates.sort(key=lambda x: x[1])

        for q, d in candidates[:k]:
            walking = max(3, round(d / 80))
            cycling = max(2, round(d / 220))
            taxi = max(5, round(5 + d / 350))
            subway_recommended = d >= 1800
            subway_minutes = max(12, round(8 + d / 450)) if subway_recommended else None
            transit_modes = ["walking", "cycling", "taxi"]
            if subway_recommended:
                transit_modes.append("subway")
            route_type_options = ["步行友好", "普通街道", "适合骑行", "打车更优"]
            if subway_recommended:
                route_type_options.append("地铁接驳")

            edge = {
                "from": p["id"],
                "to": q["id"],
                "distance_meters": round(d),
                "walking_minutes": walking,
                "cycling_minutes": cycling,
                "taxi_minutes": taxi,
                "subway_recommended": subway_recommended,
                "subway_minutes": subway_minutes,
                "subway_transfer_count": random.choice([0, 0, 1]) if subway_recommended else 0,
                "transit_modes": transit_modes,
                "route_type": random.choice(route_type_options),
                "scenic_score": round(random.uniform(3.0, 4.8), 1),
                "shade_score": round(random.uniform(2.8, 4.7), 1),
                "crowd_level": random.choice(["low", "medium", "high"]),
                "suitable_weather": random.choice([
                    ["晴天", "阴天"],
                    ["晴天", "阴天", "雨天"],
                    ["晴天"]
                ]),
                "energy_cost": random.choice([1, 1, 2, 2, 3]),
                "route_note": "距离较近，适合串联成周末路线。" if not subway_recommended else "距离略长，可以结合地铁接驳，减少连续步行压力。"
            }
            edges.append(edge)

    for poi in pois:
        poi.pop("_grid_cell", None)

    return edges

def generate_feedback_samples(pois, n=60):
    samples = []
    positive_templates = [
        "体验不错，环境很舒服。",
        "很适合聊天，下次还会来。",
        "比预期更放松，路线安排也不累。",
        "拍照很好看，适合周末慢慢逛。"
    ]
    negative_templates = [
        "周末人有点多，体验一般。",
        "有点吵，不太适合放松。",
        "距离有点远，下次希望少走路。",
        "价格略高，预算有限的话不太推荐。"
    ]

    for i in range(n):
        poi = random.choice(pois)
        sentiment = random.choices(["positive", "neutral", "negative"], weights=[0.65, 0.20, 0.15])[0]
        raw = random.choice(positive_templates if sentiment == "positive" else negative_templates)

        samples.append({
            "feedback_id": f"fb_{i+1:03d}",
            "user_id": f"user_{random.randint(1, 8):03d}",
            "poi_id": poi["id"],
            "sentiment": sentiment,
            "raw_feedback": f"{poi['name']}：{raw}",
            "tags_added": random.sample(poi["mood_tags"], min(2, len(poi["mood_tags"]))),
            "issues": [] if sentiment == "positive" else random.sample(["拥挤", "太吵", "距离远", "价格高", "排队"], 2),
            "created_at": "2026-05-01T21:00:00"
        })
    return samples

def generate_user_profiles():
    return [
        {
            "user_id": "user_001",
            "name": "松弛独处型",
            "explicit_preferences": {
                "likes": ["咖啡", "书店", "安静", "松弛", "低步行", "室内"],
                "dislikes": ["排队", "太吵", "太贵", "高强度运动"],
                "budget_preference": "medium",
                "max_walking_minutes_per_segment": 15
            },
            "learned_weights": {
                "咖啡": 1.3,
                "书店": 1.4,
                "安静": 1.5,
                "松弛": 1.4,
                "低步行": 1.6,
                "热闹": 0.7
            }
        },
        {
            "user_id": "user_002",
            "name": "朋友社交型",
            "explicit_preferences": {
                "likes": ["桌游", "手作体验", "甜品", "互动", "新鲜"],
                "dislikes": ["太安静", "无聊", "独处"],
                "budget_preference": "medium",
                "max_walking_minutes_per_segment": 20
            },
            "learned_weights": {
                "桌游": 1.4,
                "手作体验": 1.5,
                "互动": 1.4,
                "新鲜": 1.3,
                "安静": 0.8
            }
        },
        {
            "user_id": "user_003",
            "name": "约会拍照型",
            "explicit_preferences": {
                "likes": ["展览", "甜品", "茶馆", "拍照", "约会", "氛围感"],
                "dislikes": ["太吵", "太挤", "停车困难"],
                "budget_preference": "high",
                "max_walking_minutes_per_segment": 18
            },
            "learned_weights": {
                "展览": 1.4,
                "甜品": 1.2,
                "拍照": 1.6,
                "约会": 1.5,
                "拥挤": 0.6
            }
        }
    ]

def main():
    input_file = Path(os.environ.get("SHENZHEN_INPUT_FILE", INPUT_FILE))
    rows = read_input_rows(input_file)
    total_rows = len(rows)

    bounds = (
        min(row["Lon"] for row in rows),
        max(row["Lon"] for row in rows),
        min(row["Lat"] for row in rows),
        max(row["Lat"] for row in rows)
    )

    sample_size = min(get_sample_size(), total_rows)
    rows = random.sample(rows, sample_size)

    pois = [generate_poi(row, i + 1, bounds) for i, row in enumerate(rows)]
    edges = generate_edges(pois, k=NEIGHBOR_COUNT)
    feedback = generate_feedback_samples(pois, n=60)
    users = generate_user_profiles()

    (OUTPUT_DIR / "poi.json").write_text(json.dumps(pois, ensure_ascii=False, indent=2), encoding="utf-8")
    (OUTPUT_DIR / "route_edges.json").write_text(json.dumps(edges, ensure_ascii=False, indent=2), encoding="utf-8")
    (OUTPUT_DIR / "feedback.json").write_text(json.dumps(feedback, ensure_ascii=False, indent=2), encoding="utf-8")
    (OUTPUT_DIR / "user_profiles.json").write_text(json.dumps(users, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Sampled {len(rows)} rows from {total_rows} input rows")
    print(f"Generated {len(pois)} POIs")
    print(f"Generated {len(edges)} route edges")
    print(f"Generated {len(feedback)} feedback samples")
    print(f"Generated {len(users)} user profiles")

if __name__ == "__main__":
    main()
