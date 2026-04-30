from typing import Any

from local_explorer_agent.app.domain.models import POI, ExperienceScores
from local_explorer_agent.app.repositories.json_repository import JSONRepository


class POIRepository(JSONRepository):
    filename = "poi.sample.json"
    supplement_filenames = ["poi.intent_supplement.json"]

    def list_all(self) -> list[POI]:
        records = list(self.load_json(self.filename))
        for filename in self.supplement_filenames:
            records.extend(self.load_json(filename, default=[]))
        return [self._to_poi(item) for item in _dedupe_by_id(records)]

    def get(self, poi_id: str) -> POI | None:
        return next((poi for poi in self.list_all() if poi.id == poi_id), None)

    def search(
        self,
        *,
        city: str | None = None,
        tags: list[str] | None = None,
        categories: list[str] | None = None,
        indoor: bool | None = None,
        max_queue_risk: str | None = None,
        limit: int = 5,
        priority_categories: list[str] | None = None,
    ) -> list[POI]:
        return search_pois(
            self.list_all(),
            city=city,
            tags=tags,
            categories=categories,
            indoor=indoor,
            max_queue_risk=max_queue_risk,
            limit=limit,
            priority_categories=priority_categories,
        )

    def _to_poi(self, item: dict[str, Any]) -> POI:
        if "experience_scores" not in item:
            item = {
                **item,
                "experience_scores": ExperienceScores(
                    photo_score=item.get("photo_score", 0),
                    conversation_score=item.get("conversation_score", 0),
                    novelty_score=item.get("novelty_score", 0),
                    relax_score=item.get("relax_score", 0),
                ).model_dump(),
            }
        return POI.model_validate(item)


def _as_string_set(values: list[str] | str | None) -> set[str]:
    terms: set[str] = set()
    if values is None:
        return terms
    raw_values = [values] if isinstance(values, str) else values
    for raw in raw_values:
        if not isinstance(raw, str):
            continue
        value = raw.strip()
        if not value:
            continue
        terms.add(value)
    return terms


def search_pois(
    pois: list[POI],
    *,
    city: str | None = None,
    tags: list[str] | None = None,
    categories: list[str] | None = None,
    indoor: bool | None = None,
    max_queue_risk: str | None = None,
    limit: int = 5,
    priority_categories: list[str] | None = None,
) -> list[POI]:
    categories_set = _as_string_set(categories)
    tags_set = _as_string_set(tags)
    priority_rank = {
        category: index
        for index, category in enumerate(priority_categories or [])
        if isinstance(category, str) and category.strip()
    }
    default_priority_rank = len(priority_rank)

    if city:
        pois = [poi for poi in pois if poi.city == city]
    if indoor is not None:
        pois = [poi for poi in pois if poi.indoor is indoor]
    if max_queue_risk == "low":
        pois = [poi for poi in pois if poi.queue_risk == "low"]

    if categories_set:
        category_matches = [poi for poi in pois if poi.category in categories_set]
        if category_matches:
            pois = category_matches
        elif tags_set:
            tag_matches = [poi for poi in pois if tags_set.intersection(_poi_terms(poi))]
            if tag_matches:
                pois = tag_matches
    elif tags_set:
        tag_matches = [poi for poi in pois if tags_set.intersection(_poi_terms(poi))]
        if tag_matches:
            pois = tag_matches

    risk_rank = {"low": 0, "medium": 1, "high": 2}

    def sort_key(poi: POI) -> tuple[int, int, int, float, int]:
        return (
            priority_rank.get(poi.category, default_priority_rank),
            risk_rank.get(poi.queue_risk, 1),
            -len(tags_set.intersection(_poi_terms(poi))),
            -poi.experience_scores.relax_score,
            poi.avg_price or 0,
        )

    pois.sort(key=sort_key)
    return pois[:limit]


def _dedupe_by_id(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_id: dict[str, dict[str, Any]] = {}
    for record in records:
        record_id = record.get("id") if isinstance(record, dict) else None
        if not record_id:
            continue
        by_id[record_id] = record
    return list(by_id.values())


def _poi_terms(poi: POI) -> set[str]:
    return set(
        [
            poi.category,
            poi.area or "",
            *(poi.activity_tags + poi.mood_tags + poi.suitable_for + poi.conflict_relief_tags),
        ]
    )
