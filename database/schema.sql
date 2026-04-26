CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS poi (
    id TEXT PRIMARY KEY,
    source_instance INTEGER,
    source_feature TEXT,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    city TEXT NOT NULL,
    area TEXT,
    lon DOUBLE PRECISION NOT NULL,
    lat DOUBLE PRECISION NOT NULL,
    location GEOGRAPHY(Point, 4326)
        GENERATED ALWAYS AS (ST_SetSRID(ST_MakePoint(lon, lat), 4326)::GEOGRAPHY) STORED,
    address TEXT,
    avg_price INTEGER,
    open_hours TEXT,
    avg_stay_minutes INTEGER,
    reservation_required BOOLEAN NOT NULL DEFAULT FALSE,
    indoor BOOLEAN NOT NULL DEFAULT TRUE,
    weather_fit JSONB NOT NULL DEFAULT '[]'::JSONB,
    energy_level SMALLINT,
    crowd_risk TEXT,
    queue_risk TEXT,
    mood_tags JSONB NOT NULL DEFAULT '[]'::JSONB,
    activity_tags JSONB NOT NULL DEFAULT '[]'::JSONB,
    suitable_for JSONB NOT NULL DEFAULT '[]'::JSONB,
    avoid_for JSONB NOT NULL DEFAULT '[]'::JSONB,
    photo_score NUMERIC(3, 1),
    conversation_score NUMERIC(3, 1),
    novelty_score NUMERIC(3, 1),
    relax_score NUMERIC(3, 1),
    description TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS poi_facilities (
    poi_id TEXT PRIMARY KEY REFERENCES poi(id) ON DELETE CASCADE,
    restroom BOOLEAN NOT NULL DEFAULT FALSE,
    pet_friendly BOOLEAN NOT NULL DEFAULT FALSE,
    charging_available BOOLEAN NOT NULL DEFAULT FALSE,
    wifi BOOLEAN NOT NULL DEFAULT FALSE,
    accessible BOOLEAN NOT NULL DEFAULT FALSE,
    baby_care_room BOOLEAN NOT NULL DEFAULT FALSE,
    luggage_storage BOOLEAN NOT NULL DEFAULT FALSE,
    air_conditioning BOOLEAN NOT NULL DEFAULT FALSE,
    seating_quality TEXT,
    raw JSONB NOT NULL DEFAULT '{}'::JSONB,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS poi_transportation (
    poi_id TEXT PRIMARY KEY REFERENCES poi(id) ON DELETE CASCADE,
    subway_station TEXT,
    subway_lines JSONB NOT NULL DEFAULT '[]'::JSONB,
    subway_exit TEXT,
    subway_distance_meters INTEGER,
    subway_walk_minutes INTEGER,
    subway_recommended BOOLEAN NOT NULL DEFAULT FALSE,
    last_train_buffer_minutes INTEGER,
    subway_access_note TEXT,
    bus_distance_meters INTEGER,
    parking_available BOOLEAN NOT NULL DEFAULT FALSE,
    parking_fee TEXT,
    bike_parking_available BOOLEAN NOT NULL DEFAULT FALSE,
    taxi_dropoff_friendly BOOLEAN NOT NULL DEFAULT FALSE,
    walking_difficulty TEXT,
    raw JSONB NOT NULL DEFAULT '{}'::JSONB,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS poi_business_rules (
    poi_id TEXT PRIMARY KEY REFERENCES poi(id) ON DELETE CASCADE,
    photo_allowed BOOLEAN NOT NULL DEFAULT FALSE,
    outside_food_allowed BOOLEAN NOT NULL DEFAULT FALSE,
    group_buy_available BOOLEAN NOT NULL DEFAULT FALSE,
    reservation_required BOOLEAN NOT NULL DEFAULT FALSE,
    takeaway_allowed BOOLEAN NOT NULL DEFAULT FALSE,
    refund_friendly BOOLEAN NOT NULL DEFAULT FALSE,
    min_spend INTEGER NOT NULL DEFAULT 0,
    time_limit_minutes INTEGER,
    age_restriction TEXT,
    dress_code TEXT,
    quiet_required BOOLEAN NOT NULL DEFAULT FALSE,
    pets_allowed_inside BOOLEAN NOT NULL DEFAULT FALSE,
    raw JSONB NOT NULL DEFAULT '{}'::JSONB,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS route_edges (
    id BIGSERIAL PRIMARY KEY,
    from_poi_id TEXT NOT NULL REFERENCES poi(id) ON DELETE CASCADE,
    to_poi_id TEXT NOT NULL REFERENCES poi(id) ON DELETE CASCADE,
    distance_meters INTEGER NOT NULL,
    walking_minutes INTEGER,
    cycling_minutes INTEGER,
    taxi_minutes INTEGER,
    subway_recommended BOOLEAN NOT NULL DEFAULT FALSE,
    subway_minutes INTEGER,
    subway_transfer_count SMALLINT NOT NULL DEFAULT 0,
    transit_modes JSONB NOT NULL DEFAULT '[]'::JSONB,
    route_type TEXT,
    scenic_score NUMERIC(3, 1),
    shade_score NUMERIC(3, 1),
    crowd_level TEXT,
    suitable_weather JSONB NOT NULL DEFAULT '[]'::JSONB,
    energy_cost SMALLINT,
    route_note TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT route_edges_from_to_uniq UNIQUE (from_poi_id, to_poi_id),
    CONSTRAINT route_edges_not_self CHECK (from_poi_id <> to_poi_id)
);

CREATE TABLE IF NOT EXISTS user_profiles (
    user_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    likes JSONB NOT NULL DEFAULT '[]'::JSONB,
    dislikes JSONB NOT NULL DEFAULT '[]'::JSONB,
    budget_preference TEXT,
    max_walking_minutes_per_segment INTEGER,
    explicit_preferences JSONB NOT NULL DEFAULT '{}'::JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS user_preference_weights (
    user_id TEXT NOT NULL REFERENCES user_profiles(user_id) ON DELETE CASCADE,
    preference_key TEXT NOT NULL,
    weight NUMERIC(6, 3) NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (user_id, preference_key)
);

CREATE TABLE IF NOT EXISTS route_plans (
    route_plan_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT REFERENCES user_profiles(user_id) ON DELETE SET NULL,
    title TEXT,
    status TEXT NOT NULL DEFAULT 'draft',
    plan_date DATE,
    start_time TIME,
    total_distance_meters INTEGER,
    total_duration_minutes INTEGER,
    total_budget INTEGER,
    weather_context JSONB NOT NULL DEFAULT '{}'::JSONB,
    preference_snapshot JSONB NOT NULL DEFAULT '{}'::JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS route_stops (
    route_stop_id BIGSERIAL PRIMARY KEY,
    route_plan_id UUID NOT NULL REFERENCES route_plans(route_plan_id) ON DELETE CASCADE,
    poi_id TEXT NOT NULL REFERENCES poi(id) ON DELETE CASCADE,
    stop_order INTEGER NOT NULL,
    planned_arrival_at TIMESTAMPTZ,
    planned_departure_at TIMESTAMPTZ,
    stay_minutes INTEGER,
    note TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT route_stops_plan_order_uniq UNIQUE (route_plan_id, stop_order)
);

CREATE TABLE IF NOT EXISTS feedback (
    feedback_id TEXT PRIMARY KEY,
    user_id TEXT,
    poi_id TEXT NOT NULL REFERENCES poi(id) ON DELETE CASCADE,
    sentiment TEXT NOT NULL,
    raw_feedback TEXT NOT NULL,
    tags_added JSONB NOT NULL DEFAULT '[]'::JSONB,
    issues JSONB NOT NULL DEFAULT '[]'::JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS poi_feedback_summary (
    poi_id TEXT PRIMARY KEY REFERENCES poi(id) ON DELETE CASCADE,
    feedback_count INTEGER NOT NULL DEFAULT 0,
    positive_rate NUMERIC(5, 4),
    common_praises JSONB NOT NULL DEFAULT '[]'::JSONB,
    common_issues JSONB NOT NULL DEFAULT '[]'::JSONB,
    tag_votes JSONB NOT NULL DEFAULT '{}'::JSONB,
    photo_score_adjustment NUMERIC(4, 2) NOT NULL DEFAULT 0,
    conversation_score_adjustment NUMERIC(4, 2) NOT NULL DEFAULT 0,
    novelty_score_adjustment NUMERIC(4, 2) NOT NULL DEFAULT 0,
    relax_score_adjustment NUMERIC(4, 2) NOT NULL DEFAULT 0,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS poi_location_gix ON poi USING GIST (location);
CREATE INDEX IF NOT EXISTS poi_city_category_idx ON poi (city, category);
CREATE INDEX IF NOT EXISTS poi_area_idx ON poi (area);
CREATE INDEX IF NOT EXISTS poi_avg_price_idx ON poi (avg_price);
CREATE INDEX IF NOT EXISTS poi_mood_tags_gin ON poi USING GIN (mood_tags);
CREATE INDEX IF NOT EXISTS poi_activity_tags_gin ON poi USING GIN (activity_tags);
CREATE INDEX IF NOT EXISTS poi_transportation_subway_lines_gin ON poi_transportation USING GIN (subway_lines);
CREATE INDEX IF NOT EXISTS route_edges_from_idx ON route_edges (from_poi_id);
CREATE INDEX IF NOT EXISTS route_edges_to_idx ON route_edges (to_poi_id);
CREATE INDEX IF NOT EXISTS route_edges_subway_idx ON route_edges (subway_recommended);
CREATE INDEX IF NOT EXISTS user_preference_weights_key_idx ON user_preference_weights (preference_key);
CREATE INDEX IF NOT EXISTS route_plans_user_idx ON route_plans (user_id);
CREATE INDEX IF NOT EXISTS route_stops_plan_idx ON route_stops (route_plan_id, stop_order);
CREATE INDEX IF NOT EXISTS feedback_poi_idx ON feedback (poi_id);
CREATE INDEX IF NOT EXISTS feedback_user_idx ON feedback (user_id);
