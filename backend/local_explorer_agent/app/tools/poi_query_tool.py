import time
from dataclasses import dataclass
from typing import Any

from local_explorer_agent.app.domain.models import POI
from local_explorer_agent.app.repositories.poi_repository import POIRepository
from local_explorer_agent.app.tools.base import BaseTool, ToolResult


@dataclass(frozen=True)
class _IntentRule:
    triggers: tuple[str, ...]
    categories: tuple[str, ...] = ()
    tags: tuple[str, ...] = ()


_INTENT_RULES: tuple[_IntentRule, ...] = (
    _IntentRule(
        triggers=("烧烤",),
        categories=("烧烤",),
        tags=("烧烤", "聚餐", "社交", "吃饭"),
    ),
    _IntentRule(
        triggers=("火锅",),
        categories=("火锅",),
        tags=("火锅", "聚餐", "社交", "吃饭"),
    ),
    _IntentRule(
        triggers=("烤肉",),
        categories=("烤肉", "烧烤"),
        tags=("烤肉", "烧烤", "聚餐", "社交", "吃饭"),
    ),
    _IntentRule(
        triggers=("游乐园", "游乐场", "乐园"),
        categories=("游乐园",),
        tags=("游乐园", "刺激", "亲子", "互动", "释放体力"),
    ),
    _IntentRule(
        triggers=("密室逃脱", "密室", "逃脱"),
        categories=("密室逃脱",),
        tags=("密室逃脱", "刺激", "互动", "社交"),
    ),
    _IntentRule(
        triggers=("桌游",),
        categories=("桌游",),
        tags=("桌游", "互动", "社交", "聚会"),
    ),
    _IntentRule(
        triggers=("小剧场", "脱口秀", "黑盒剧场", "剧场", "演出"),
        categories=("小剧场",),
        tags=("小剧场", "脱口秀", "演出", "文艺", "夜间"),
    ),
    _IntentRule(
        triggers=("情侣", "约会", "二人世界", "对象", "女朋友", "男朋友"),
        categories=("展览", "Citywalk", "买手店", "咖啡", "甜品", "茶馆"),
        tags=("情侣", "约会", "浪漫", "聊天", "拍照", "有氛围"),
    ),
    _IntentRule(
        triggers=("手作", "陶艺", "皮具", "银饰"),
        categories=("手作体验",),
        tags=("手作", "互动", "约会", "室内"),
    ),
    _IntentRule(
        triggers=("买手店", "vintage", "小店"),
        categories=("买手店",),
        tags=("拍照", "文艺", "约会", "小众"),
    ),
    _IntentRule(
        triggers=("展览", "看展", "逛展", "美术馆", "画展"),
        categories=("展览",),
        tags=("展览", "文艺", "拍照", "安静"),
    ),
    _IntentRule(
        triggers=("亲子空间",),
        categories=("亲子空间",),
        tags=("亲子", "互动", "安全", "室内"),
    ),
    _IntentRule(
        triggers=("孩子", "小孩", "亲子", "宝宝", "女儿", "儿子", "孩子们", "放电", "释放体力"),
        categories=("亲子空间", "公园"),
        tags=("亲子", "child", "family", "互动", "运动", "释放体力", "散步"),
    ),
    _IntentRule(
        triggers=("老人", "长辈", "爸妈", "父母", "平坦", "步道", "走走", "散步", "少走路"),
        categories=("公园", "书店", "咖啡"),
        tags=("散步", "自然", "松弛", "休息", "安静", "低刺激"),
    ),
    _IntentRule(
        triggers=("减肥", "减脂", "低卡", "健康", "清爽", "控糖", "健身", "清淡"),
        categories=("轻食",),
        tags=("轻食", "低卡", "健康", "清爽", "吃饭"),
    ),
    _IntentRule(
        triggers=("轻食",),
        categories=("轻食",),
        tags=("轻食", "低卡", "健康", "吃饭"),
    ),
    _IntentRule(
        triggers=("甜品", "蛋糕", "冰淇淋", "奶茶"),
        categories=("甜品",),
        tags=("甜品", "下午茶", "拍照", "治愈"),
    ),
    _IntentRule(
        triggers=("咖啡", "喝咖啡", "坐坐", "不折腾", "轻松"),
        categories=("咖啡", "书店", "轻食"),
        tags=("聊天", "休息", "安静", "松弛", "治愈", "低刺激"),
    ),
    _IntentRule(
        triggers=("聊天", "休息", "安静"),
        categories=("咖啡", "书店", "茶馆"),
        tags=("聊天", "休息", "安静", "松弛", "治愈", "低刺激"),
    ),
    _IntentRule(
        triggers=("拍照", "打卡", "氛围", "文艺", "好看", "新鲜", "网红点", "网红", "仪式感"),
        categories=("展览", "书店", "咖啡", "公园"),
        tags=("拍照", "文艺", "自然", "开阔", "聊天"),
    ),
    _IntentRule(
        triggers=("夜间", "下班后", "晚上", "烟火气", "夜宵", "不正式"),
        categories=("夜间活动", "烧烤", "茶馆", "咖啡"),
        tags=("夜间", "烟火气", "放松", "聊天", "社交"),
    ),
    _IntentRule(
        triggers=("预算", "便宜", "不贵", "低预算", "免费", "性价比"),
        categories=("公园", "书店", "咖啡"),
        tags=("散步", "休息", "聊天", "自然"),
    ),
    _IntentRule(
        triggers=("公园", "草坪", "户外", "自然", "晒太阳"),
        categories=("公园",),
        tags=("散步", "户外", "自然", "开阔", "松弛", "拍照"),
    ),
    _IntentRule(
        triggers=("餐厅", "吃饭", "吃点", "用餐", "晚餐", "午餐", "聚餐"),
        categories=("餐厅", "轻食"),
        tags=("吃饭", "聊天", "社交"),
    ),
)

_STAGE_DEFAULTS: dict[str, _IntentRule] = {
    "energy_release": _IntentRule(
        triggers=(),
        categories=("公园", "Citywalk", "手作体验"),
        tags=("释放体力", "互动", "运动", "散步"),
    ),
    "dine": _IntentRule(
        triggers=(),
        categories=("餐厅", "轻食", "咖啡"),
        tags=("吃饭", "轻食", "低卡", "健康", "聊天", "社交"),
    ),
    "relax": _IntentRule(
        triggers=(),
        categories=("书店", "咖啡", "公园"),
        tags=("休息", "安静", "松弛", "治愈", "低刺激", "自然"),
    ),
    "explore": _IntentRule(
        triggers=(),
        categories=("书店", "公园", "咖啡", "展览", "Citywalk"),
        tags=("拍照", "文艺", "自然", "聊天", "开阔"),
    ),
}

_CATEGORY_COMPATIBLE_EXPANSIONS: dict[str, set[str]] = {
    "餐厅": {"餐厅", "轻食", "火锅", "烧烤", "烤肉", "甜品", "咖啡", "茶馆", "桑拿鸡"},
    "轻食": {"轻食"},
    "火锅": {"火锅"},
    "烧烤": {"烧烤", "烤肉"},
    "烤肉": {"烤肉", "烧烤"},
    "甜品": {"甜品"},
    "咖啡": {"咖啡"},
    "茶馆": {"茶馆"},
    "亲子空间": {"亲子空间", "游乐园"},
    "游乐园": {"游乐园", "亲子空间"},
    "展览": {"展览"},
    "手作体验": {"手作体验"},
    "买手店": {"买手店"},
    "小剧场": {"小剧场"},
    "密室逃脱": {"密室逃脱"},
    "桌游": {"桌游"},
    "公园": {"公园", "Citywalk"},
}


class POIQueryRewriteTool(BaseTool):
    name = "poi_query_rewrite_tool"

    def __init__(self, repository: POIRepository) -> None:
        self.repository = repository

    def rewrite_stage_query(
        self,
        *,
        city: str,
        stage_type: str,
        stage_name: str,
        experience_goal: str,
        constraints: dict[str, Any],
    ) -> ToolResult:
        started_at = time.perf_counter()
        city_pois = [poi for poi in self.repository.list_all() if poi.city == city]
        if not city_pois:
            return self._result(
                success=False,
                data={
                    "city": city,
                    "categories": [],
                    "tags": [],
                    "indoor": _optional_bool(constraints.get("indoor")),
                    "max_queue_risk": "low" if constraints.get("avoid_queue") else None,
                },
                error_code="poi_taxonomy_empty",
                error_message=f"No POI taxonomy found for city {city}",
                started_at=started_at,
                mock_scenario="data_missing_or_empty",
            )

        taxonomy_categories = {poi.category for poi in city_pois}
        taxonomy_tags = _taxonomy_tags(city_pois)
        raw_categories = _string_values(
            constraints.get("categories") or constraints.get("category")
        )
        raw_tags = _string_values(constraints.get("tags") or constraints.get("标签"))
        free_text_values = _string_values(constraints)
        query_text = " ".join(
            [stage_type, stage_name, experience_goal, *raw_categories, *raw_tags, *free_text_values]
        )

        categories = _match_terms(raw_categories, taxonomy_categories)
        tags = _match_terms(raw_tags, taxonomy_tags)
        matched_rules: list[str] = []
        compatible_categories = _compatible_categories(categories)

        for rule in _INTENT_RULES:
            if any(trigger in query_text for trigger in rule.triggers):
                rule_categories = {term for term in rule.categories if term in taxonomy_categories}
                if categories:
                    categories.update(rule_categories.intersection(compatible_categories))
                else:
                    categories.update(rule_categories)
                tags.update(term for term in rule.tags if term in taxonomy_tags)
                matched_rules.extend(rule.triggers)

        if not categories and stage_type in _STAGE_DEFAULTS:
            default = _STAGE_DEFAULTS[stage_type]
            categories.update(term for term in default.categories if term in taxonomy_categories)
            tags.update(term for term in default.tags if term in taxonomy_tags)

        if not tags:
            tags.update(_fuzzy_terms(raw_categories + raw_tags + free_text_values, taxonomy_tags))
        if not categories:
            categories.update(
                _fuzzy_terms(raw_categories + raw_tags + free_text_values, taxonomy_categories)
            )

        data = {
            "city": city,
            "categories": sorted(categories),
            "tags": sorted(tags),
            "indoor": _optional_bool(constraints.get("indoor")),
            "avoid_queue": bool(constraints.get("avoid_queue")),
            "max_queue_risk": "low" if constraints.get("avoid_queue") else None,
            "raw_categories": raw_categories,
            "raw_tags": raw_tags,
            "matched_rules": sorted(set(matched_rules)),
            "taxonomy_size": {
                "categories": len(taxonomy_categories),
                "tags": len(taxonomy_tags),
            },
        }
        return self._result(data=data, started_at=started_at)


def _taxonomy_tags(pois: list[POI]) -> set[str]:
    terms: set[str] = set()
    for poi in pois:
        terms.update(
            [
                poi.category,
                poi.area or "",
                *poi.activity_tags,
                *poi.mood_tags,
                *poi.suitable_for,
                *poi.conflict_relief_tags,
            ]
        )
    return {term for term in terms if term}


def _string_values(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value.strip()] if value.strip() else []
    if isinstance(value, list | tuple | set):
        values: list[str] = []
        for item in value:
            values.extend(_string_values(item))
        return values
    if isinstance(value, dict):
        values = []
        for item in value.values():
            values.extend(_string_values(item))
        return values
    return []


def _match_terms(raw_terms: list[str], taxonomy: set[str]) -> set[str]:
    matches: set[str] = set()
    for raw in raw_terms:
        if raw in taxonomy:
            matches.add(raw)
        matches.update(
            term
            for term in taxonomy
            if len(raw) >= 2 and (raw in term or term in raw)
        )
    return matches


def _compatible_categories(categories: set[str]) -> set[str]:
    compatible = set(categories)
    for category in categories:
        compatible.update(_CATEGORY_COMPATIBLE_EXPANSIONS.get(category, {category}))
    return compatible


def _fuzzy_terms(raw_terms: list[str], taxonomy: set[str]) -> set[str]:
    matches: set[str] = set()
    for raw in raw_terms:
        raw_chars = _meaningful_chars(raw)
        if not raw_chars:
            continue
        for term in taxonomy:
            term_chars = _meaningful_chars(term)
            overlap = raw_chars.intersection(term_chars)
            if len(overlap) >= 2 and len(overlap) / max(len(term_chars), 1) >= 0.45:
                matches.add(term)
    return matches


def _meaningful_chars(value: str) -> set[str]:
    ignored = set(" 的了和与并或去想要最好别不太有点一个一些适合")
    return {char for char in value if char.strip() and char not in ignored}


def _optional_bool(value: Any) -> bool | None:
    return value if isinstance(value, bool) else None
