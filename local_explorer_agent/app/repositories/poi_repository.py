from typing import Any

from local_explorer_agent.app.domain.models import POI, ExperienceScores
from local_explorer_agent.app.repositories.json_repository import JSONRepository


class POIRepository(JSONRepository):
    filename = "poi.sample.json"

    def list_all(self) -> list[POI]:
        return [self._to_poi(item) for item in self.load_json(self.filename)]

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
    ) -> list[POI]:
        pois = self.list_all()
        if city:
            pois = [poi for poi in pois if poi.city == city]
        if categories:
            pois = [poi for poi in pois if poi.category in categories]
        if indoor is not None:
            pois = [poi for poi in pois if poi.indoor is indoor]
        if tags:
            tag_set = set(tags)
            pois = [
                poi
                for poi in pois
                if tag_set.intersection(
                    set(
                        poi.activity_tags
                        + poi.mood_tags
                        + poi.suitable_for
                        + poi.conflict_relief_tags
                    )
                )
            ]
        if max_queue_risk == "low":
            pois = [poi for poi in pois if poi.queue_risk == "low"]

        risk_rank = {"low": 0, "medium": 1, "high": 2}
        pois.sort(
            key=lambda poi: (
                risk_rank.get(poi.queue_risk, 1),
                -poi.experience_scores.relax_score,
                poi.avg_price or 0,
            )
        )
        return pois[:limit]

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
