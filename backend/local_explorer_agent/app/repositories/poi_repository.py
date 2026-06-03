from typing import TYPE_CHECKING, Any

from local_explorer_agent.app.domain.models import POI, ExperienceScores
from local_explorer_agent.app.domain.place_feedback import PlaceFeedbackSummary
from local_explorer_agent.app.repositories.json_repository import JSONRepository

if TYPE_CHECKING:
    from local_explorer_agent.app.repositories.place_feedback_repository import (
        PlaceFeedbackRepository,
    )


class POIRepository(JSONRepository):
    filename = "poi.sample.json"
    supplement_filenames = ["poi.intent_supplement.json"]

    def __init__(
        self,
        data_dir,
        *,
        place_feedback_repository: "PlaceFeedbackRepository | None" = None,
    ) -> None:
        super().__init__(data_dir)
        self.place_feedback_repository = place_feedback_repository

    def list_all(self) -> list[POI]:
        records = list(self.load_json(self.filename))
        for filename in self.supplement_filenames:
            records.extend(self.load_json(filename, default=[]))
        return [self._to_poi(item) for item in _dedupe_by_id(records)]

    def get(self, poi_id: str) -> POI | None:
        poi = next((item for item in self.list_all() if item.id == poi_id), None)
        if poi is None:
            return None
        summaries = _feedback_summaries(self.place_feedback_repository, [poi])
        return _attach_feedback_summaries([poi], summaries)[0]

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
        pois = self.list_all()
        summaries = _feedback_summaries(self.place_feedback_repository, pois)
        results = search_pois(
            pois,
            city=city,
            tags=tags,
            categories=categories,
            indoor=indoor,
            max_queue_risk=max_queue_risk,
            limit=limit,
            priority_categories=priority_categories,
            place_feedback_summaries=summaries,
        )
        return _attach_feedback_summaries(results, summaries)

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
    place_feedback_summaries: dict[str, PlaceFeedbackSummary] | None = None,
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

    def sort_key(poi: POI) -> tuple[int, int, int, float, float, int]:
        feedback_summary = (
            place_feedback_summaries.get(poi.id) if place_feedback_summaries else None
        )
        return (
            priority_rank.get(poi.category, default_priority_rank),
            risk_rank.get(poi.queue_risk, 1),
            -len(tags_set.intersection(_poi_terms(poi))),
            -_place_feedback_score(feedback_summary),
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


def _feedback_summaries(
    repository: "PlaceFeedbackRepository | None",
    pois: list[POI],
) -> dict[str, PlaceFeedbackSummary]:
    if repository is None:
        return {}
    return repository.get_summaries([poi.id for poi in pois])


def _attach_feedback_summaries(
    pois: list[POI],
    summaries: dict[str, PlaceFeedbackSummary],
) -> list[POI]:
    enriched: list[POI] = []
    for poi in pois:
        summary = summaries.get(poi.id)
        if summary is None or summary.feedback_count == 0:
            enriched.append(poi)
            continue
        business_rules = {
            **poi.business_rules,
            "user_feedback_summary": summary.model_dump(exclude_none=True),
        }
        enriched.append(poi.model_copy(update={"business_rules": business_rules}))
    return enriched


def _place_feedback_score(summary: PlaceFeedbackSummary | None) -> float:
    if summary is None or summary.feedback_count == 0 or summary.avg_rating is None:
        return 0.0
    rating_component = (summary.avg_rating - 3.0) / 2.0
    volume_component = min(summary.feedback_count, 5) / 5
    sentiment_component = 0.15 * (summary.positive_count - summary.negative_count)
    score = rating_component * (0.5 + volume_component) + sentiment_component
    return max(-1.5, min(1.5, score))
