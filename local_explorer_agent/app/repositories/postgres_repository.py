import json
from decimal import Decimal
from typing import Any

from local_explorer_agent.app.domain.models import POI, ExperienceScores
from local_explorer_agent.app.repositories.poi_repository import search_pois


class PostgresRepository:
    def __init__(self, database_url: str | None, connect_timeout: float = 3) -> None:
        if not database_url:
            raise RuntimeError("DATA_BACKEND=postgres requires DATABASE_URL.")
        self.database_url = database_url
        self.connect_timeout = connect_timeout

    def connect(self):
        try:
            import psycopg
            from psycopg.rows import dict_row
        except ImportError as exc:
            raise RuntimeError('PostgreSQL backend requires `psycopg[binary]`.') from exc

        return psycopg.connect(
            self.database_url,
            connect_timeout=int(self.connect_timeout),
            row_factory=dict_row,
        )


class PostgresPOIRepository(PostgresRepository):
    _select_sql = """
        SELECT
            p.id, p.name, p.category, p.city, p.area, p.address, p.lon, p.lat,
            p.avg_price, p.open_hours, p.avg_stay_minutes, p.indoor, p.weather_fit,
            p.energy_level, p.crowd_risk, p.queue_risk, p.mood_tags, p.activity_tags,
            p.suitable_for, p.photo_score, p.conversation_score, p.novelty_score,
            p.relax_score, f.raw AS facilities_raw, b.raw AS business_rules_raw
        FROM poi p
        LEFT JOIN poi_facilities f ON f.poi_id = p.id
        LEFT JOIN poi_business_rules b ON b.poi_id = p.id
    """

    def list_all(self) -> list[POI]:
        with self.connect() as conn:
            rows = conn.execute(f"{self._select_sql} ORDER BY p.id").fetchall()
        return [self._row_to_poi(row) for row in rows]

    def get(self, poi_id: str) -> POI | None:
        with self.connect() as conn:
            row = conn.execute(f"{self._select_sql} WHERE p.id = %s", (poi_id,)).fetchone()
        return self._row_to_poi(row) if row else None

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

    def _row_to_poi(self, row: dict[str, Any]) -> POI:
        scores = ExperienceScores(
            photo_score=_float_value(row.get("photo_score")),
            conversation_score=_float_value(row.get("conversation_score")),
            novelty_score=_float_value(row.get("novelty_score")),
            relax_score=_float_value(row.get("relax_score")),
        )
        return POI.model_validate(
            {
                "id": row["id"],
                "name": row["name"],
                "category": row["category"],
                "city": row["city"],
                "area": row.get("area"),
                "address": row.get("address"),
                "lon": _float_value(row["lon"]),
                "lat": _float_value(row["lat"]),
                "avg_price": row.get("avg_price"),
                "open_hours": row.get("open_hours"),
                "avg_stay_minutes": row.get("avg_stay_minutes"),
                "indoor": row.get("indoor", True),
                "weather_fit": _json_list(row.get("weather_fit")),
                "energy_level": row.get("energy_level") or 1,
                "crowd_risk": row.get("crowd_risk") or "medium",
                "queue_risk": row.get("queue_risk") or "medium",
                "suitable_for": _json_list(row.get("suitable_for")),
                "activity_tags": _json_list(row.get("activity_tags")),
                "mood_tags": _json_list(row.get("mood_tags")),
                "experience_scores": scores.model_dump(),
                "facilities": _json_value(row.get("facilities_raw"), {}),
                "business_rules": _json_value(row.get("business_rules_raw"), {}),
            }
        )


class PostgresRouteRepository(PostgresRepository):
    def list_all(self) -> list[dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT
                    from_poi_id, to_poi_id, distance_meters, walking_minutes,
                    cycling_minutes, taxi_minutes, subway_recommended, subway_minutes,
                    subway_transfer_count, transit_modes, route_type, scenic_score,
                    shade_score, crowd_level, suitable_weather, energy_cost, route_note
                FROM route_edges
                ORDER BY id
                """
            ).fetchall()
        return [self._row_to_route(row) for row in rows]

    def get_route(self, from_poi_id: str, to_poi_id: str) -> dict[str, Any] | None:
        with self.connect() as conn:
            row = conn.execute(
                """
                SELECT
                    from_poi_id, to_poi_id, distance_meters, walking_minutes,
                    cycling_minutes, taxi_minutes, subway_recommended, subway_minutes,
                    subway_transfer_count, transit_modes, route_type, scenic_score,
                    shade_score, crowd_level, suitable_weather, energy_cost, route_note
                FROM route_edges
                WHERE from_poi_id = %s AND to_poi_id = %s
                """,
                (from_poi_id, to_poi_id),
            ).fetchone()
            if row:
                return self._row_to_route(row)

            row = conn.execute(
                """
                SELECT
                    from_poi_id, to_poi_id, distance_meters, walking_minutes,
                    cycling_minutes, taxi_minutes, subway_recommended, subway_minutes,
                    subway_transfer_count, transit_modes, route_type, scenic_score,
                    shade_score, crowd_level, suitable_weather, energy_cost, route_note
                FROM route_edges
                WHERE from_poi_id = %s AND to_poi_id = %s
                """,
                (to_poi_id, from_poi_id),
            ).fetchone()

        if not row:
            return None
        return {**self._row_to_route(row), "from": from_poi_id, "to": to_poi_id}

    def _row_to_route(self, row: dict[str, Any]) -> dict[str, Any]:
        return {
            "from": row["from_poi_id"],
            "to": row["to_poi_id"],
            "distance_meters": row.get("distance_meters"),
            "walking_minutes": row.get("walking_minutes"),
            "cycling_minutes": row.get("cycling_minutes"),
            "taxi_minutes": row.get("taxi_minutes"),
            "subway_recommended": row.get("subway_recommended", False),
            "subway_minutes": row.get("subway_minutes"),
            "subway_transfer_count": row.get("subway_transfer_count", 0),
            "transit_modes": _json_list(row.get("transit_modes")),
            "route_type": row.get("route_type"),
            "scenic_score": _optional_float(row.get("scenic_score")),
            "shade_score": _optional_float(row.get("shade_score")),
            "crowd_level": row.get("crowd_level"),
            "suitable_weather": _json_list(row.get("suitable_weather")),
            "energy_cost": row.get("energy_cost"),
            "route_note": row.get("route_note"),
        }


class PostgresQueueRepository(PostgresRepository):
    def list_all(self) -> list[dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT poi_id, queue_minutes, risk, mock_scenario
                FROM queue_status
                ORDER BY poi_id
                """
            ).fetchall()
        return [dict(row) for row in rows]

    def get_status(self, poi_id: str) -> dict[str, Any]:
        with self.connect() as conn:
            row = conn.execute(
                """
                SELECT poi_id, queue_minutes, risk, mock_scenario
                FROM queue_status
                WHERE poi_id = %s
                """,
                (poi_id,),
            ).fetchone()
            if row:
                return dict(row)

            poi_row = conn.execute("SELECT queue_risk FROM poi WHERE id = %s", (poi_id,)).fetchone()

        risk = poi_row["queue_risk"] if poi_row else "medium"
        return {
            "poi_id": poi_id,
            "queue_minutes": {"low": 5, "medium": 15, "high": 35}.get(risk, 10),
            "risk": risk,
            "mock_scenario": "derived_from_poi",
        }


def _json_value(value: Any, default: Any) -> Any:
    if value is None:
        return default
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return default
    return value


def _json_list(value: Any) -> list[Any]:
    parsed = _json_value(value, [])
    return parsed if isinstance(parsed, list) else []


def _float_value(value: Any) -> float:
    return float(value) if isinstance(value, Decimal) else float(value or 0)


def _optional_float(value: Any) -> float | None:
    if value is None:
        return None
    return float(value) if isinstance(value, Decimal) else float(value)
