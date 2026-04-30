from local_explorer_agent.app.core.config import get_settings
from local_explorer_agent.app.repositories.poi_repository import POIRepository
from local_explorer_agent.app.tools.poi_query_tool import POIQueryRewriteTool
from local_explorer_agent.app.tools.poi_tool import POITool


def _tools() -> tuple[POIQueryRewriteTool, POITool]:
    settings = get_settings()
    data_dir = settings.data_dir if settings.data_dir.is_absolute() else settings.data_dir.resolve()
    repository = POIRepository(data_dir)
    return POIQueryRewriteTool(repository), POITool(repository)


def test_poi_query_rewrite_maps_elder_walk_need_to_park_terms() -> None:
    rewrite_tool, poi_tool = _tools()

    rewrite = rewrite_tool.rewrite_stage_query(
        city="深圳",
        stage_type="relax",
        stage_name="老人孩子公园走走",
        experience_goal="平坦步道、休息设施、安静环境，适合老人和孩子慢慢走",
        constraints={
            "tags": ["平坦步道", "休息设施", "安静环境"],
            "categories": ["公园"],
            "avoid_queue": True,
        },
    )

    assert rewrite.success is True
    query = rewrite.data
    assert "公园" in query["categories"]
    assert {"散步", "自然"}.intersection(query["tags"])

    result = poi_tool.search_poi(
        city=query["city"],
        tags=query["tags"],
        categories=query["categories"],
        max_queue_risk=query["max_queue_risk"],
        limit=4,
    )

    assert result.success is True
    assert result.data
    assert any(poi.category == "公园" for poi in result.data)


def test_poi_query_rewrite_maps_photo_budget_friend_need_to_local_taxonomy() -> None:
    rewrite_tool, poi_tool = _tools()

    rewrite = rewrite_tool.rewrite_stage_query(
        city="深圳",
        stage_type="explore",
        stage_name="朋友拍照咖啡",
        experience_goal="想拍照但别太折腾，预算别太高，最好有点氛围",
        constraints={"tags": ["拍照氛围", "低预算", "不折腾"], "avoid_queue": True},
    )

    query = rewrite.data
    assert {"书店", "咖啡", "公园"}.intersection(query["categories"])
    assert {"拍照", "文艺", "聊天", "休息"}.intersection(query["tags"])

    result = poi_tool.search_poi(
        city=query["city"],
        tags=query["tags"],
        categories=query["categories"],
        max_queue_risk=query["max_queue_risk"],
        limit=4,
    )

    assert result.success is True
    assert result.data


def test_poi_query_rewrite_maps_diet_need_to_light_food() -> None:
    rewrite_tool, poi_tool = _tools()

    rewrite = rewrite_tool.rewrite_stage_query(
        city="深圳",
        stage_type="dine",
        stage_name="减脂友好用餐",
        experience_goal="老婆最近在减肥，希望低卡但不要被特殊对待",
        constraints={"tags": ["减脂", "低热量", "健康餐"], "categories": ["餐厅"]},
    )

    query = rewrite.data
    assert "轻食" in query["categories"]
    assert {"轻食", "低卡", "健康"}.intersection(query["tags"])

    result = poi_tool.search_poi(
        city=query["city"],
        tags=query["tags"],
        categories=query["categories"],
        limit=4,
    )

    assert result.success is True
    assert result.data
    assert result.data[0].category == "轻食"
    assert {"轻食", "低卡", "健康"}.intersection(
        set(result.data[0].activity_tags + result.data[0].mood_tags)
    )


def test_poi_query_rewrite_keeps_light_food_from_becoming_park() -> None:
    rewrite_tool, _ = _tools()

    rewrite = rewrite_tool.rewrite_stage_query(
        city="深圳",
        stage_type="dine",
        stage_name="自然低卡用餐",
        experience_goal="把减脂约束融入普通家庭用餐，不制造心理负担",
        constraints={
            "标签": ["轻食", "低卡", "聊天"],
            "categories": ["轻食"],
            "low_calorie": True,
            "avoid_queue": True,
        },
    )

    query = rewrite.data
    assert "轻食" in query["categories"]
    assert "公园" not in query["categories"]
    assert "茶馆" not in query["categories"]


def test_poi_query_rewrite_maps_theater_and_talk_show() -> None:
    rewrite_tool, poi_tool = _tools()

    rewrite = rewrite_tool.rewrite_stage_query(
        city="深圳",
        stage_type="explore",
        stage_name="晚上看小剧场",
        experience_goal="周末晚上想看个小剧场或者脱口秀，结束后简单吃点",
        constraints={"tags": ["小剧场", "脱口秀"], "avoid_queue": True},
    )

    query = rewrite.data
    assert "小剧场" in query["categories"]

    result = poi_tool.search_poi(
        city=query["city"],
        tags=query["tags"],
        categories=query["categories"],
        limit=4,
        priority_categories=["小剧场"],
    )

    assert result.success is True
    assert result.data
    assert result.data[0].category == "小剧场"


def test_poi_query_rewrite_maps_night_smoke_to_social_food() -> None:
    rewrite_tool, _ = _tools()

    rewrite = rewrite_tool.rewrite_stage_query(
        city="深圳",
        stage_type="dine",
        stage_name="夜间烟火气聚餐",
        experience_goal="下班后朋友想找个夜间活动，能放松聊天，有点烟火气",
        constraints={"tags": ["夜间", "烟火气", "聊天"]},
    )

    query = rewrite.data
    assert {"烧烤", "夜间活动", "茶馆", "咖啡"}.intersection(query["categories"])
