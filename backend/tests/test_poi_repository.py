from local_explorer_agent.app.core.config import get_settings
from local_explorer_agent.app.repositories.poi_repository import POIRepository


def test_poi_search_relaxes_llm_style_tags_for_park() -> None:
    settings = get_settings()
    data_dir = settings.data_dir if settings.data_dir.is_absolute() else settings.data_dir.resolve()
    repository = POIRepository(data_dir)

    results = repository.search(
        city="深圳",
        tags=["平坦步道", "休息设施", "安静环境"],
        categories=["公园"],
        max_queue_risk="low",
        limit=4,
    )

    assert results
    assert all(poi.category == "公园" for poi in results)
    assert all(poi.queue_risk == "low" for poi in results)
    assert {"散步", "休息", "自然"}.intersection(
        set(results[0].activity_tags + results[0].mood_tags)
    )


def test_poi_search_keeps_category_pool_when_tags_do_not_exactly_match() -> None:
    settings = get_settings()
    data_dir = settings.data_dir if settings.data_dir.is_absolute() else settings.data_dir.resolve()
    repository = POIRepository(data_dir)

    results = repository.search(
        city="深圳",
        tags=["完全不存在的标签"],
        categories=["公园"],
        max_queue_risk="low",
        limit=4,
    )

    assert results
    assert all(poi.category == "公园" for poi in results)
    assert all(poi.queue_risk == "low" for poi in results)


def test_poi_search_priority_category_beats_generic_relax_places() -> None:
    settings = get_settings()
    data_dir = settings.data_dir if settings.data_dir.is_absolute() else settings.data_dir.resolve()
    repository = POIRepository(data_dir)

    results = repository.search(
        city="深圳",
        tags=["聊天", "休息", "自然", "低卡", "轻食"],
        categories=["公园", "茶馆", "轻食", "餐厅"],
        limit=6,
        priority_categories=["轻食"],
    )

    assert results
    assert results[0].category == "轻食"


def test_poi_repository_loads_intent_supplement_data() -> None:
    settings = get_settings()
    data_dir = settings.data_dir if settings.data_dir.is_absolute() else settings.data_dir.resolve()
    repository = POIRepository(data_dir)

    categories = [poi.category for poi in repository.list_all() if poi.city == "深圳"]

    assert categories.count("烤肉") >= 5
    assert categories.count("密室逃脱") >= 5
    assert categories.count("小剧场") >= 5
    assert categories.count("亲子空间") >= 5
    assert categories.count("游乐园") >= 5
