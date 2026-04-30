import argparse
import json
import os
from pathlib import Path

DEFAULT_DATA_DIR = Path(__file__).resolve().parents[1] / "local_explorer_agent" / "app" / "data"
DEFAULT_SCHEMA_FILE = Path(__file__).resolve().parent / "schema.sql"


class ChineseHelpFormatter(argparse.HelpFormatter):
    def _format_usage(self, usage, actions, groups, prefix):
        return super()._format_usage(usage, actions, groups, "用法: ")


def load_json(data_dir, filename):
    return json.loads((data_dir / filename).read_text(encoding="utf-8"))


def load_optional_json(data_dir, filename, default):
    path = data_dir / filename
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def merge_records_by_key(records, supplements, key):
    by_key = {}
    for record in [*records, *supplements]:
        record_key = record.get(key) if isinstance(record, dict) else None
        if not record_key:
            continue
        by_key[record_key] = record
    return list(by_key.values())


def as_jsonb(value):
    from psycopg.types.json import Jsonb

    return Jsonb(value if value is not None else {})


def execute_schema(conn, schema_file):
    conn.execute(schema_file.read_text(encoding="utf-8"))


def truncate_generated_tables(conn):
    conn.execute(
        """
        TRUNCATE TABLE
            route_stops,
            route_plans,
            feedback,
            queue_status,
            route_edges,
            user_preference_weights,
            user_profiles,
            poi_feedback_summary,
            poi_business_rules,
            poi_transportation,
            poi_facilities,
            poi
        RESTART IDENTITY CASCADE
        """
    )


def upsert_pois(conn, pois):
    poi_sql = """
        INSERT INTO poi (
            id, source_instance, source_feature, name, category, city, area, lon, lat,
            address, avg_price, open_hours, avg_stay_minutes, reservation_required,
            indoor, weather_fit, energy_level, crowd_risk, queue_risk, mood_tags,
            activity_tags, suitable_for, avoid_for, photo_score, conversation_score,
            novelty_score, relax_score, description, updated_at
        )
        VALUES (
            %(id)s, %(source_instance)s, %(source_feature)s, %(name)s, %(category)s,
            %(city)s, %(area)s, %(lon)s, %(lat)s, %(address)s, %(avg_price)s,
            %(open_hours)s, %(avg_stay_minutes)s, %(reservation_required)s,
            %(indoor)s, %(weather_fit)s, %(energy_level)s, %(crowd_risk)s,
            %(queue_risk)s, %(mood_tags)s, %(activity_tags)s, %(suitable_for)s,
            %(avoid_for)s, %(photo_score)s, %(conversation_score)s, %(novelty_score)s,
            %(relax_score)s, %(description)s, NOW()
        )
        ON CONFLICT (id) DO UPDATE SET
            source_instance = EXCLUDED.source_instance,
            source_feature = EXCLUDED.source_feature,
            name = EXCLUDED.name,
            category = EXCLUDED.category,
            city = EXCLUDED.city,
            area = EXCLUDED.area,
            lon = EXCLUDED.lon,
            lat = EXCLUDED.lat,
            address = EXCLUDED.address,
            avg_price = EXCLUDED.avg_price,
            open_hours = EXCLUDED.open_hours,
            avg_stay_minutes = EXCLUDED.avg_stay_minutes,
            reservation_required = EXCLUDED.reservation_required,
            indoor = EXCLUDED.indoor,
            weather_fit = EXCLUDED.weather_fit,
            energy_level = EXCLUDED.energy_level,
            crowd_risk = EXCLUDED.crowd_risk,
            queue_risk = EXCLUDED.queue_risk,
            mood_tags = EXCLUDED.mood_tags,
            activity_tags = EXCLUDED.activity_tags,
            suitable_for = EXCLUDED.suitable_for,
            avoid_for = EXCLUDED.avoid_for,
            photo_score = EXCLUDED.photo_score,
            conversation_score = EXCLUDED.conversation_score,
            novelty_score = EXCLUDED.novelty_score,
            relax_score = EXCLUDED.relax_score,
            description = EXCLUDED.description,
            updated_at = NOW()
    """

    facility_sql = """
        INSERT INTO poi_facilities (
            poi_id, restroom, pet_friendly, charging_available, wifi, accessible,
            baby_care_room, luggage_storage, air_conditioning, seating_quality, raw,
            updated_at
        )
        VALUES (
            %(poi_id)s, %(restroom)s, %(pet_friendly)s, %(charging_available)s,
            %(wifi)s, %(accessible)s, %(baby_care_room)s, %(luggage_storage)s,
            %(air_conditioning)s, %(seating_quality)s, %(raw)s, NOW()
        )
        ON CONFLICT (poi_id) DO UPDATE SET
            restroom = EXCLUDED.restroom,
            pet_friendly = EXCLUDED.pet_friendly,
            charging_available = EXCLUDED.charging_available,
            wifi = EXCLUDED.wifi,
            accessible = EXCLUDED.accessible,
            baby_care_room = EXCLUDED.baby_care_room,
            luggage_storage = EXCLUDED.luggage_storage,
            air_conditioning = EXCLUDED.air_conditioning,
            seating_quality = EXCLUDED.seating_quality,
            raw = EXCLUDED.raw,
            updated_at = NOW()
    """

    transportation_sql = """
        INSERT INTO poi_transportation (
            poi_id, subway_station, subway_lines, subway_exit, subway_distance_meters,
            subway_walk_minutes, subway_recommended, last_train_buffer_minutes,
            subway_access_note, bus_distance_meters, parking_available, parking_fee,
            bike_parking_available, taxi_dropoff_friendly, walking_difficulty, raw,
            updated_at
        )
        VALUES (
            %(poi_id)s, %(subway_station)s, %(subway_lines)s, %(subway_exit)s,
            %(subway_distance_meters)s, %(subway_walk_minutes)s,
            %(subway_recommended)s, %(last_train_buffer_minutes)s,
            %(subway_access_note)s, %(bus_distance_meters)s, %(parking_available)s,
            %(parking_fee)s, %(bike_parking_available)s, %(taxi_dropoff_friendly)s,
            %(walking_difficulty)s, %(raw)s, NOW()
        )
        ON CONFLICT (poi_id) DO UPDATE SET
            subway_station = EXCLUDED.subway_station,
            subway_lines = EXCLUDED.subway_lines,
            subway_exit = EXCLUDED.subway_exit,
            subway_distance_meters = EXCLUDED.subway_distance_meters,
            subway_walk_minutes = EXCLUDED.subway_walk_minutes,
            subway_recommended = EXCLUDED.subway_recommended,
            last_train_buffer_minutes = EXCLUDED.last_train_buffer_minutes,
            subway_access_note = EXCLUDED.subway_access_note,
            bus_distance_meters = EXCLUDED.bus_distance_meters,
            parking_available = EXCLUDED.parking_available,
            parking_fee = EXCLUDED.parking_fee,
            bike_parking_available = EXCLUDED.bike_parking_available,
            taxi_dropoff_friendly = EXCLUDED.taxi_dropoff_friendly,
            walking_difficulty = EXCLUDED.walking_difficulty,
            raw = EXCLUDED.raw,
            updated_at = NOW()
    """

    business_rules_sql = """
        INSERT INTO poi_business_rules (
            poi_id, photo_allowed, outside_food_allowed, group_buy_available,
            reservation_required, takeaway_allowed, refund_friendly, min_spend,
            time_limit_minutes, age_restriction, dress_code, quiet_required,
            pets_allowed_inside, raw, updated_at
        )
        VALUES (
            %(poi_id)s, %(photo_allowed)s, %(outside_food_allowed)s,
            %(group_buy_available)s, %(reservation_required)s, %(takeaway_allowed)s,
            %(refund_friendly)s, %(min_spend)s, %(time_limit_minutes)s,
            %(age_restriction)s, %(dress_code)s, %(quiet_required)s,
            %(pets_allowed_inside)s, %(raw)s, NOW()
        )
        ON CONFLICT (poi_id) DO UPDATE SET
            photo_allowed = EXCLUDED.photo_allowed,
            outside_food_allowed = EXCLUDED.outside_food_allowed,
            group_buy_available = EXCLUDED.group_buy_available,
            reservation_required = EXCLUDED.reservation_required,
            takeaway_allowed = EXCLUDED.takeaway_allowed,
            refund_friendly = EXCLUDED.refund_friendly,
            min_spend = EXCLUDED.min_spend,
            time_limit_minutes = EXCLUDED.time_limit_minutes,
            age_restriction = EXCLUDED.age_restriction,
            dress_code = EXCLUDED.dress_code,
            quiet_required = EXCLUDED.quiet_required,
            pets_allowed_inside = EXCLUDED.pets_allowed_inside,
            raw = EXCLUDED.raw,
            updated_at = NOW()
    """

    feedback_summary_sql = """
        INSERT INTO poi_feedback_summary (
            poi_id, feedback_count, positive_rate, common_praises, common_issues,
            tag_votes, photo_score_adjustment, conversation_score_adjustment,
            novelty_score_adjustment, relax_score_adjustment, updated_at
        )
        VALUES (
            %(poi_id)s, %(feedback_count)s, %(positive_rate)s, %(common_praises)s,
            %(common_issues)s, %(tag_votes)s, %(photo_score_adjustment)s,
            %(conversation_score_adjustment)s, %(novelty_score_adjustment)s,
            %(relax_score_adjustment)s, NOW()
        )
        ON CONFLICT (poi_id) DO UPDATE SET
            feedback_count = EXCLUDED.feedback_count,
            positive_rate = EXCLUDED.positive_rate,
            common_praises = EXCLUDED.common_praises,
            common_issues = EXCLUDED.common_issues,
            tag_votes = EXCLUDED.tag_votes,
            photo_score_adjustment = EXCLUDED.photo_score_adjustment,
            conversation_score_adjustment = EXCLUDED.conversation_score_adjustment,
            novelty_score_adjustment = EXCLUDED.novelty_score_adjustment,
            relax_score_adjustment = EXCLUDED.relax_score_adjustment,
            updated_at = NOW()
    """

    for poi in pois:
        scores = poi.get("experience_scores", {})
        rules = poi.get("business_rules", {})
        conn.execute(
            poi_sql,
            {
                **poi,
                "source_instance": poi.get("source_instance"),
                "source_feature": poi.get("source_feature"),
                "area": poi.get("area"),
                "address": poi.get("address"),
                "avg_price": poi.get("avg_price"),
                "open_hours": poi.get("open_hours"),
                "avg_stay_minutes": poi.get("avg_stay_minutes"),
                "reservation_required": poi.get(
                    "reservation_required", rules.get("reservation_required", False)
                ),
                "indoor": poi.get("indoor", True),
                "weather_fit": as_jsonb(poi.get("weather_fit", [])),
                "energy_level": poi.get("energy_level", 1),
                "crowd_risk": poi.get("crowd_risk", "medium"),
                "queue_risk": poi.get("queue_risk", "medium"),
                "mood_tags": as_jsonb(poi.get("mood_tags", [])),
                "activity_tags": as_jsonb(poi.get("activity_tags", [])),
                "suitable_for": as_jsonb(poi.get("suitable_for", [])),
                "avoid_for": as_jsonb(poi.get("avoid_for", [])),
                "photo_score": poi.get("photo_score", scores.get("photo_score", 0)),
                "conversation_score": poi.get(
                    "conversation_score", scores.get("conversation_score", 0)
                ),
                "novelty_score": poi.get("novelty_score", scores.get("novelty_score", 0)),
                "relax_score": poi.get("relax_score", scores.get("relax_score", 0)),
                "description": poi.get("description"),
            },
        )

        facilities = poi.get("facilities", {})
        conn.execute(
            facility_sql,
            {
                "poi_id": poi["id"],
                "restroom": facilities.get("restroom", False),
                "pet_friendly": facilities.get("pet_friendly", False),
                "charging_available": facilities.get("charging_available", False),
                "wifi": facilities.get("wifi", False),
                "accessible": facilities.get("accessible", False),
                "baby_care_room": facilities.get("baby_care_room", False),
                "luggage_storage": facilities.get("luggage_storage", False),
                "air_conditioning": facilities.get("air_conditioning", False),
                "seating_quality": facilities.get("seating_quality"),
                "raw": as_jsonb(facilities),
            },
        )

        transportation = poi.get("transportation", {})
        subway = transportation.get("subway", {})
        conn.execute(
            transportation_sql,
            {
                "poi_id": poi["id"],
                "subway_station": (
                    transportation.get("subway_station") or subway.get("nearest_station")
                ),
                "subway_lines": as_jsonb(
                    transportation.get("subway_lines") or subway.get("lines", [])
                ),
                "subway_exit": transportation.get("subway_exit") or subway.get("exit"),
                "subway_distance_meters": (
                    transportation.get("subway_distance_meters") or subway.get("distance_meters")
                ),
                "subway_walk_minutes": (
                    transportation.get("subway_walk_minutes") or subway.get("walk_minutes")
                ),
                "subway_recommended": subway.get("recommended", False),
                "last_train_buffer_minutes": subway.get("last_train_buffer_minutes"),
                "subway_access_note": subway.get("access_note"),
                "bus_distance_meters": transportation.get("bus_distance_meters"),
                "parking_available": transportation.get("parking_available", False),
                "parking_fee": transportation.get("parking_fee"),
                "bike_parking_available": transportation.get("bike_parking_available", False),
                "taxi_dropoff_friendly": transportation.get("taxi_dropoff_friendly", False),
                "walking_difficulty": transportation.get("walking_difficulty"),
                "raw": as_jsonb(transportation),
            },
        )

        rules = poi.get("business_rules", {})
        conn.execute(
            business_rules_sql,
            {
                "poi_id": poi["id"],
                "photo_allowed": rules.get("photo_allowed", False),
                "outside_food_allowed": rules.get("outside_food_allowed", False),
                "group_buy_available": rules.get("group_buy_available", False),
                "reservation_required": rules.get("reservation_required", False),
                "takeaway_allowed": rules.get("takeaway_allowed", False),
                "refund_friendly": rules.get("refund_friendly", False),
                "min_spend": rules.get("min_spend", 0),
                "time_limit_minutes": rules.get("time_limit_minutes"),
                "age_restriction": rules.get("age_restriction"),
                "dress_code": rules.get("dress_code"),
                "quiet_required": rules.get("quiet_required", False),
                "pets_allowed_inside": rules.get("pets_allowed_inside", False),
                "raw": as_jsonb(rules),
            },
        )

        summary = poi.get("community_feedback", {})
        adjustments = summary.get("score_adjustments", {})
        conn.execute(
            feedback_summary_sql,
            {
                "poi_id": poi["id"],
                "feedback_count": summary.get("feedback_count", 0),
                "positive_rate": summary.get("positive_rate"),
                "common_praises": as_jsonb(summary.get("common_praises", [])),
                "common_issues": as_jsonb(summary.get("common_issues", [])),
                "tag_votes": as_jsonb(summary.get("tag_votes", {})),
                "photo_score_adjustment": adjustments.get("photo_score", 0),
                "conversation_score_adjustment": adjustments.get("conversation_score", 0),
                "novelty_score_adjustment": adjustments.get("novelty_score", 0),
                "relax_score_adjustment": adjustments.get("relax_score", 0),
            },
        )


def upsert_route_edges(conn, edges):
    sql = """
        INSERT INTO route_edges (
            from_poi_id, to_poi_id, distance_meters, walking_minutes, cycling_minutes,
            taxi_minutes, subway_recommended, subway_minutes, subway_transfer_count,
            transit_modes, route_type, scenic_score, shade_score, crowd_level,
            suitable_weather, energy_cost, route_note
        )
        VALUES (
            %(from_poi_id)s, %(to_poi_id)s, %(distance_meters)s, %(walking_minutes)s,
            %(cycling_minutes)s, %(taxi_minutes)s, %(subway_recommended)s,
            %(subway_minutes)s, %(subway_transfer_count)s, %(transit_modes)s,
            %(route_type)s, %(scenic_score)s, %(shade_score)s, %(crowd_level)s,
            %(suitable_weather)s, %(energy_cost)s, %(route_note)s
        )
        ON CONFLICT (from_poi_id, to_poi_id) DO UPDATE SET
            distance_meters = EXCLUDED.distance_meters,
            walking_minutes = EXCLUDED.walking_minutes,
            cycling_minutes = EXCLUDED.cycling_minutes,
            taxi_minutes = EXCLUDED.taxi_minutes,
            subway_recommended = EXCLUDED.subway_recommended,
            subway_minutes = EXCLUDED.subway_minutes,
            subway_transfer_count = EXCLUDED.subway_transfer_count,
            transit_modes = EXCLUDED.transit_modes,
            route_type = EXCLUDED.route_type,
            scenic_score = EXCLUDED.scenic_score,
            shade_score = EXCLUDED.shade_score,
            crowd_level = EXCLUDED.crowd_level,
            suitable_weather = EXCLUDED.suitable_weather,
            energy_cost = EXCLUDED.energy_cost,
            route_note = EXCLUDED.route_note
    """

    for edge in edges:
        conn.execute(
            sql,
            {
                "from_poi_id": edge["from"],
                "to_poi_id": edge["to"],
                "distance_meters": edge.get("distance_meters"),
                "walking_minutes": edge.get("walking_minutes"),
                "cycling_minutes": edge.get("cycling_minutes"),
                "taxi_minutes": edge.get("taxi_minutes"),
                "subway_recommended": edge.get("subway_recommended", False),
                "subway_minutes": edge.get("subway_minutes"),
                "subway_transfer_count": edge.get("subway_transfer_count", 0),
                "transit_modes": as_jsonb(edge.get("transit_modes", [])),
                "route_type": edge.get("route_type"),
                "scenic_score": edge.get("scenic_score"),
                "shade_score": edge.get("shade_score"),
                "crowd_level": edge.get("crowd_level"),
                "suitable_weather": as_jsonb(edge.get("suitable_weather", [])),
                "energy_cost": edge.get("energy_cost"),
                "route_note": edge.get("route_note"),
            },
        )


def upsert_queue_status(conn, statuses):
    sql = """
        INSERT INTO queue_status (poi_id, queue_minutes, risk, mock_scenario, updated_at)
        VALUES (%(poi_id)s, %(queue_minutes)s, %(risk)s, %(mock_scenario)s, NOW())
        ON CONFLICT (poi_id) DO UPDATE SET
            queue_minutes = EXCLUDED.queue_minutes,
            risk = EXCLUDED.risk,
            mock_scenario = EXCLUDED.mock_scenario,
            updated_at = NOW()
    """

    for item in statuses:
        conn.execute(
            sql,
            {
                "poi_id": item["poi_id"],
                "queue_minutes": item.get("queue_minutes", 10),
                "risk": item.get("risk", "medium"),
                "mock_scenario": item.get("mock_scenario"),
            },
        )


def upsert_user_profiles(conn, users):
    profile_sql = """
        INSERT INTO user_profiles (
            user_id, name, likes, dislikes, budget_preference,
            max_walking_minutes_per_segment, explicit_preferences, updated_at
        )
        VALUES (
            %(user_id)s, %(name)s, %(likes)s, %(dislikes)s, %(budget_preference)s,
            %(max_walking_minutes_per_segment)s, %(explicit_preferences)s, NOW()
        )
        ON CONFLICT (user_id) DO UPDATE SET
            name = EXCLUDED.name,
            likes = EXCLUDED.likes,
            dislikes = EXCLUDED.dislikes,
            budget_preference = EXCLUDED.budget_preference,
            max_walking_minutes_per_segment = EXCLUDED.max_walking_minutes_per_segment,
            explicit_preferences = EXCLUDED.explicit_preferences,
            updated_at = NOW()
    """

    weight_sql = """
        INSERT INTO user_preference_weights (user_id, preference_key, weight, updated_at)
        VALUES (%(user_id)s, %(preference_key)s, %(weight)s, NOW())
        ON CONFLICT (user_id, preference_key) DO UPDATE SET
            weight = EXCLUDED.weight,
            updated_at = NOW()
    """

    for user in users:
        preferences = user.get("explicit_preferences", {})
        conn.execute(
            profile_sql,
            {
                "user_id": user["user_id"],
                "name": user["name"],
                "likes": as_jsonb(preferences.get("likes", [])),
                "dislikes": as_jsonb(preferences.get("dislikes", [])),
                "budget_preference": preferences.get("budget_preference"),
                "max_walking_minutes_per_segment": preferences.get(
                    "max_walking_minutes_per_segment"
                ),
                "explicit_preferences": as_jsonb(preferences),
            },
        )

        conn.execute("DELETE FROM user_preference_weights WHERE user_id = %s", (user["user_id"],))
        for key, weight in user.get("learned_weights", {}).items():
            conn.execute(
                weight_sql,
                {
                    "user_id": user["user_id"],
                    "preference_key": key,
                    "weight": weight,
                },
            )


def upsert_feedback(conn, feedback_items):
    sql = """
        INSERT INTO feedback (
            feedback_id, user_id, poi_id, sentiment, raw_feedback, tags_added,
            issues, created_at
        )
        VALUES (
            %(feedback_id)s, %(user_id)s, %(poi_id)s, %(sentiment)s,
            %(raw_feedback)s, %(tags_added)s, %(issues)s, %(created_at)s
        )
        ON CONFLICT (feedback_id) DO UPDATE SET
            user_id = EXCLUDED.user_id,
            poi_id = EXCLUDED.poi_id,
            sentiment = EXCLUDED.sentiment,
            raw_feedback = EXCLUDED.raw_feedback,
            tags_added = EXCLUDED.tags_added,
            issues = EXCLUDED.issues,
            created_at = EXCLUDED.created_at
    """

    for item in feedback_items:
        conn.execute(
            sql,
            {
                "feedback_id": item["feedback_id"],
                "user_id": item.get("user_id"),
                "poi_id": item["poi_id"],
                "sentiment": item["sentiment"],
                "raw_feedback": item["raw_feedback"],
                "tags_added": as_jsonb(item.get("tags_added", [])),
                "issues": as_jsonb(item.get("issues", [])),
                "created_at": item.get("created_at"),
            },
        )


def parse_args():
    parser = argparse.ArgumentParser(
        description="把生成的 Weekend Agent JSON 数据导入 PostgreSQL。",
        usage="python3 database/import_generated_data.py [选项]",
        add_help=False,
        formatter_class=ChineseHelpFormatter,
    )
    parser._optionals.title = "选项"
    parser.add_argument("-h", "--help", action="help", help="显示帮助信息并退出。")
    parser.add_argument(
        "--database-url",
        default=os.environ.get("DATABASE_URL"),
        help="PostgreSQL 连接地址，例如 postgresql://postgres:postgres@localhost:5432/weekend_agent",
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=DEFAULT_DATA_DIR,
        help="生成 JSON 文件所在目录。",
    )
    parser.add_argument(
        "--schema-file",
        type=Path,
        default=DEFAULT_SCHEMA_FILE,
        help="数据库表结构 SQL 文件路径。",
    )
    parser.add_argument(
        "--init-schema",
        action="store_true",
        help="导入前先执行 database/schema.sql 初始化表结构。",
    )
    parser.add_argument("--truncate", action="store_true", help="导入前清空生成数据相关表。")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="只读取 JSON 并打印数量，不连接 PostgreSQL。",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    data_dir = args.data_dir.resolve()
    pois = merge_records_by_key(
        load_json(data_dir, "poi.json"),
        load_optional_json(data_dir, "poi.intent_supplement.json", []),
        "id",
    )
    edges = load_json(data_dir, "route_edges.json")
    queue_status = merge_records_by_key(
        load_optional_json(data_dir, "queue_status.json", []),
        load_optional_json(data_dir, "queue_status.intent_supplement.json", []),
        "poi_id",
    )
    users = load_optional_json(data_dir, "user_profiles.json", [])
    feedback_items = load_optional_json(data_dir, "feedback.json", [])

    if args.dry_run:
        print(f"已读取 {len(pois)} 条 POI")
        print(f"已读取 {len(edges)} 条路线边")
        print(f"已读取 {len(queue_status)} 条排队状态")
        print(f"已读取 {len(users)} 条用户画像")
        print(f"已读取 {len(feedback_items)} 条反馈")
        return

    try:
        import psycopg
    except ImportError as exc:
        raise SystemExit('缺少依赖：请先执行 `python3 -m pip install "psycopg[binary]"`。') from exc

    if not args.database_url:
        raise SystemExit("需要设置 DATABASE_URL，或通过 --database-url 传入数据库连接地址。")

    with psycopg.connect(args.database_url) as conn:
        if args.init_schema:
            execute_schema(conn, args.schema_file)
        if args.truncate:
            truncate_generated_tables(conn)

        upsert_pois(conn, pois)
        upsert_route_edges(conn, edges)
        upsert_queue_status(conn, queue_status)
        upsert_user_profiles(conn, users)
        upsert_feedback(conn, feedback_items)

    print(f"已导入 {len(pois)} 条 POI")
    print(f"已导入 {len(edges)} 条路线边")
    print(f"已导入 {len(queue_status)} 条排队状态")
    print(f"已导入 {len(users)} 条用户画像")
    print(f"已导入 {len(feedback_items)} 条反馈")


if __name__ == "__main__":
    main()
