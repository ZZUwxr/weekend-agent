# Weekend Agent 数据库设计文档

本文档说明 Weekend Agent 项目的数据库结构、表关系、字段设计、数据导入方式和数据生成思路。当前方案使用 PostgreSQL + PostGIS，适合后续接入 FastAPI、Node.js、Supabase 或其他前后端交互服务。

## 当前状态

本地已经在 conda 环境 `weekend-agent` 中初始化过一个 PostgreSQL 实例，并导入过当前生成数据。

当前数据库实例默认不随应用自动启动；需要查询或导入数据时，先按“启动和关闭”章节启动。

当前本地数据库连接地址：

```bash
postgresql://wxr@localhost:5433/weekend_agent
```

本地数据库文件位于：

```bash
database/pgdata
```

该目录已被 [database/.gitignore](.gitignore) 忽略，不应提交到代码仓库。

最近一次导入数据量：

| 表名 | 行数 | 说明 |
| --- | ---: | --- |
| `poi` | 117 | 新生成路线包里的真实感 POI |
| `poi_facilities` | 117 | 每个 POI 的设施数据 |
| `poi_transportation` | 117 | 每个 POI 的交通与停车数据 |
| `poi_business_rules` | 117 | 每个 POI 的经营规则 |
| `route_edges` | 88 | 新生成路线包里的 POI 连接边 |
| `queue_status` | 117 | 新生成 POI 的排队状态 |
| `user_profiles` | 0 | 用户画像等待真实用户系统写入 |
| `user_preference_weights` | 0 | 用户偏好权重等待真实用户系统写入 |
| `route_plans` | 0 | 用户路线记录，等待业务写入 |
| `route_stops` | 0 | 路线站点记录，等待业务写入 |
| `feedback` | 0 | 用户反馈等待业务写入 |
| `poi_feedback_summary` | 117 | POI 聚合反馈摘要 |

## 启动和关闭

启动本地数据库：

```bash
conda run -n weekend-agent pg_ctl -D database/pgdata -l database/postgres.log -o "-p 5433 -k /tmp" start
```

停止本地数据库：

```bash
conda run -n weekend-agent pg_ctl -D database/pgdata stop
```

查看数据库状态：

```bash
conda run -n weekend-agent pg_ctl -D database/pgdata status
```

连接数据库：

```bash
conda run -n weekend-agent psql "postgresql://wxr@localhost:5433/weekend_agent"
```

## 初始化和导入

如果需要重新初始化表结构并用当前新生成数据替换数据库内容：

```bash
conda run -n weekend-agent python database/import_generated_data.py \
  --database-url "postgresql://wxr@localhost:5433/weekend_agent" \
  --init-schema \
 --truncate
```

后端运行时读取数据库需要在 `.env` 中开启：

```bash
DATA_BACKEND=postgres
DATABASE_URL=postgresql://wxr@localhost:5433/weekend_agent
```

只校验 JSON 能否被读取，不连接数据库：

```bash
conda run -n weekend-agent python database/import_generated_data.py --dry-run
```

如果使用外部 PostgreSQL，可以设置自己的连接地址：

```bash
export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/weekend_agent"
python3 database/import_generated_data.py --database-url "$DATABASE_URL" --init-schema --truncate
```

## 总体设计思路

数据库以 `poi` 为核心，围绕“地点推荐”和“周末路线规划”拆成 4 类数据：

| 数据域 | 对应表 | 设计目的 |
| --- | --- | --- |
| POI 静态信息 | `poi`、`poi_facilities`、`poi_transportation`、`poi_business_rules` | 存储地点本身、设施、交通、规则等可用于筛选和展示的信息 |
| POI 图结构 | `route_edges` | 表示地点之间是否适合串联，以及步行、骑行、打车、地铁等连接成本 |
| 用户偏好 | `user_profiles`、`user_preference_weights` | 存储用户显式偏好和可学习的推荐权重 |
| 用户路线和反馈 | `route_plans`、`route_stops`、`feedback`、`poi_feedback_summary` | 支持用户生成路线、保存路线、游后反馈和公共口碑聚合 |

设计上采用“关系表 + JSONB”的混合模式：

- 高频筛选字段使用普通列，例如 `category`、`avg_price`、`indoor`、`subway_walk_minutes`。
- 可扩展的标签、列表和半结构化信息使用 `jsonb`，例如 `mood_tags`、`activity_tags`、`subway_lines`、`transit_modes`。
- 经纬度使用 `lon`、`lat` 保存原始数值，同时生成 PostGIS `location` 字段，方便做附近搜索和距离排序。
- POI 的大类信息拆到多个一对一扩展表，避免 `poi` 表过宽，也方便后续按模块维护。

## 数据来源和构造思路

当前导入数据来自已经转换好的应用数据目录：

```bash
local_explorer_agent/app/data/poi.json
local_explorer_agent/app/data/poi.intent_supplement.json
local_explorer_agent/app/data/route_edges.json
local_explorer_agent/app/data/queue_status.json
local_explorer_agent/app/data/queue_status.intent_supplement.json
```

这些文件由新生成路线包转换而来：

```bash
data_process/generated_route_packs_30calls
data_process/convert_route_packs_to_system_data.py
```

`*.intent_supplement.json` 存放意图匹配补充数据，用于补齐烤肉、密室逃脱、小剧场、亲子空间、游乐园等稀缺类别；导入脚本会与主数据按 ID 合并后 upsert 到 PostgreSQL。

导入脚本默认只读取非 sample 文件；没有 `user_profiles.json` 或 `feedback.json` 时，对应表保持为空，避免旧示例数据混入新数据集。

## 表关系

核心关系如下：

```text
poi 1 -- 1 poi_facilities
poi 1 -- 1 poi_transportation
poi 1 -- 1 poi_business_rules
poi 1 -- 1 poi_feedback_summary
poi 1 -- 1 queue_status

poi 1 -- N route_edges.from_poi_id
poi 1 -- N route_edges.to_poi_id

user_profiles 1 -- N user_preference_weights
user_profiles 1 -- N route_plans
route_plans 1 -- N route_stops
poi 1 -- N route_stops

poi 1 -- N feedback
feedback.user_id 当前不加外键
```

`feedback.user_id` 没有设置外键，是因为生成数据里的反馈用户 ID 可能不在当前 `user_profiles` 示例用户中。正式用户系统接入后，可以改为外键。

## 扩展和索引

使用的 PostgreSQL 扩展：

| 扩展 | 用途 |
| --- | --- |
| `postgis` | 支持地理位置字段、距离计算和空间索引 |
| `pgcrypto` | 支持 `gen_random_uuid()`，用于生成路线计划 ID |

主要索引：

| 索引 | 用途 |
| --- | --- |
| `poi_location_gix` | POI 地理位置空间查询 |
| `poi_city_category_idx` | 城市和类别筛选 |
| `poi_area_idx` | 区域筛选 |
| `poi_avg_price_idx` | 价格筛选 |
| `poi_mood_tags_gin` | 情绪标签 JSONB 查询 |
| `poi_activity_tags_gin` | 活动标签 JSONB 查询 |
| `poi_transportation_subway_lines_gin` | 地铁线路 JSONB 查询 |
| `route_edges_from_idx` | 从某个 POI 查可达地点 |
| `route_edges_to_idx` | 查到达某个 POI 的路线边 |
| `route_edges_subway_idx` | 筛选建议地铁接驳的路线边 |
| `queue_status_risk_idx` | 按排队风险筛选排队状态 |
| `user_preference_weights_key_idx` | 按偏好项反查用户权重 |
| `route_plans_user_idx` | 按用户查询路线记录 |
| `route_stops_plan_idx` | 按路线读取站点顺序 |
| `feedback_poi_idx` | 按 POI 查询反馈 |
| `feedback_user_idx` | 按用户查询反馈 |

## 表结构详情

### `poi`：POI 基础表

存储地点的核心展示、筛选和评分信息。

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | `TEXT` | POI 主键，例如 `sz_poi_001` |
| `source_instance` | `INTEGER` | CSV 原始实例编号 |
| `source_feature` | `TEXT` | CSV 原始 Feature 值 |
| `name` | `TEXT` | POI 名称 |
| `category` | `TEXT` | 业务类别，例如咖啡、书店、展览 |
| `city` | `TEXT` | 城市，目前为深圳 |
| `area` | `TEXT` | 模拟业务区域 |
| `lon` | `DOUBLE PRECISION` | 经度 |
| `lat` | `DOUBLE PRECISION` | 纬度 |
| `location` | `GEOGRAPHY(Point, 4326)` | PostGIS 地理点，由经纬度自动生成 |
| `address` | `TEXT` | 地址文本 |
| `avg_price` | `INTEGER` | 人均价格 |
| `open_hours` | `TEXT` | 营业时间 |
| `avg_stay_minutes` | `INTEGER` | 建议停留分钟数 |
| `reservation_required` | `BOOLEAN` | 是否需要预约 |
| `indoor` | `BOOLEAN` | 是否室内 |
| `weather_fit` | `JSONB` | 适合天气列表 |
| `energy_level` | `SMALLINT` | 体力消耗等级 |
| `crowd_risk` | `TEXT` | 拥挤风险，取值如 `low`、`medium`、`high` |
| `queue_risk` | `TEXT` | 排队风险 |
| `mood_tags` | `JSONB` | 情绪标签 |
| `activity_tags` | `JSONB` | 活动标签 |
| `suitable_for` | `JSONB` | 适合人群 |
| `avoid_for` | `JSONB` | 不适合人群 |
| `photo_score` | `NUMERIC(3,1)` | 拍照评分 |
| `conversation_score` | `NUMERIC(3,1)` | 聊天评分 |
| `novelty_score` | `NUMERIC(3,1)` | 新鲜感评分 |
| `relax_score` | `NUMERIC(3,1)` | 放松评分 |
| `description` | `TEXT` | 面向用户展示的地点描述 |
| `created_at` | `TIMESTAMPTZ` | 创建时间 |
| `updated_at` | `TIMESTAMPTZ` | 更新时间 |

### `poi_facilities`：硬件设施表

与 `poi` 一对一，存储地点设施能力。拆表后，前端详情页或筛选页可以按需加载。

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `poi_id` | `TEXT` | POI 外键，也是主键 |
| `restroom` | `BOOLEAN` | 是否有洗手间 |
| `pet_friendly` | `BOOLEAN` | 是否宠物友好 |
| `charging_available` | `BOOLEAN` | 是否方便充电 |
| `wifi` | `BOOLEAN` | 是否有 Wi-Fi |
| `accessible` | `BOOLEAN` | 是否无障碍友好 |
| `baby_care_room` | `BOOLEAN` | 是否有母婴室 |
| `luggage_storage` | `BOOLEAN` | 是否可寄存行李 |
| `air_conditioning` | `BOOLEAN` | 是否有空调 |
| `seating_quality` | `TEXT` | 座位舒适度 |
| `raw` | `JSONB` | 原始设施 JSON 备份 |
| `updated_at` | `TIMESTAMPTZ` | 更新时间 |

### `poi_transportation`：交通停车表

与 `poi` 一对一，存储地铁、公交、停车和到达便利性。

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `poi_id` | `TEXT` | POI 外键，也是主键 |
| `subway_station` | `TEXT` | 最近地铁站 |
| `subway_lines` | `JSONB` | 可乘坐地铁线路 |
| `subway_exit` | `TEXT` | 推荐出口 |
| `subway_distance_meters` | `INTEGER` | 到地铁站距离 |
| `subway_walk_minutes` | `INTEGER` | 到地铁站步行分钟数 |
| `subway_recommended` | `BOOLEAN` | 是否推荐地铁到达 |
| `last_train_buffer_minutes` | `INTEGER` | 夜间返回建议预留时间 |
| `subway_access_note` | `TEXT` | 地铁到达说明 |
| `bus_distance_meters` | `INTEGER` | 最近公交距离 |
| `parking_available` | `BOOLEAN` | 是否可停车 |
| `parking_fee` | `TEXT` | 停车费说明 |
| `bike_parking_available` | `BOOLEAN` | 是否方便停自行车 |
| `taxi_dropoff_friendly` | `BOOLEAN` | 是否适合网约车上下车 |
| `walking_difficulty` | `TEXT` | 步行难度 |
| `raw` | `JSONB` | 原始交通 JSON 备份 |
| `updated_at` | `TIMESTAMPTZ` | 更新时间 |

### `poi_business_rules`：经营规则与消费权益表

与 `poi` 一对一，存储影响用户决策的规则类信息。

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `poi_id` | `TEXT` | POI 外键，也是主键 |
| `photo_allowed` | `BOOLEAN` | 是否允许拍照 |
| `outside_food_allowed` | `BOOLEAN` | 是否允许外带食物 |
| `group_buy_available` | `BOOLEAN` | 是否有团购 |
| `reservation_required` | `BOOLEAN` | 是否需要预约 |
| `takeaway_allowed` | `BOOLEAN` | 是否支持外带 |
| `refund_friendly` | `BOOLEAN` | 退款是否友好 |
| `min_spend` | `INTEGER` | 最低消费 |
| `time_limit_minutes` | `INTEGER` | 限时停留分钟数 |
| `age_restriction` | `TEXT` | 年龄限制 |
| `dress_code` | `TEXT` | 着装要求 |
| `quiet_required` | `BOOLEAN` | 是否要求安静 |
| `pets_allowed_inside` | `BOOLEAN` | 是否允许宠物入内 |
| `raw` | `JSONB` | 原始规则 JSON 备份 |
| `updated_at` | `TIMESTAMPTZ` | 更新时间 |

### `route_edges`：地点之间的连接边

表示两个 POI 是否适合串联，以及不同交通方式下的成本。它让 POI 数据从“点列表”变成“路线图”。

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | `BIGSERIAL` | 自增主键 |
| `from_poi_id` | `TEXT` | 起点 POI |
| `to_poi_id` | `TEXT` | 终点 POI |
| `distance_meters` | `INTEGER` | 两点直线距离近似值 |
| `walking_minutes` | `INTEGER` | 步行时间 |
| `cycling_minutes` | `INTEGER` | 骑行时间 |
| `taxi_minutes` | `INTEGER` | 打车时间 |
| `subway_recommended` | `BOOLEAN` | 是否建议地铁接驳 |
| `subway_minutes` | `INTEGER` | 地铁接驳预计时间 |
| `subway_transfer_count` | `SMALLINT` | 地铁换乘次数 |
| `transit_modes` | `JSONB` | 可用交通方式 |
| `route_type` | `TEXT` | 路线类型，例如步行友好、地铁接驳 |
| `scenic_score` | `NUMERIC(3,1)` | 沿途景观评分 |
| `shade_score` | `NUMERIC(3,1)` | 遮阴评分 |
| `crowd_level` | `TEXT` | 路线拥挤程度 |
| `suitable_weather` | `JSONB` | 适合天气 |
| `energy_cost` | `SMALLINT` | 体力成本 |
| `route_note` | `TEXT` | 路线说明 |
| `created_at` | `TIMESTAMPTZ` | 创建时间 |

约束：

- `(from_poi_id, to_poi_id)` 唯一，避免重复边。
- `from_poi_id <> to_poi_id`，避免自环。

### `user_profiles`：用户画像表

存储用户的显式偏好和基础约束，用于推荐系统入口。

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `user_id` | `TEXT` | 用户主键 |
| `name` | `TEXT` | 用户画像名称 |
| `likes` | `JSONB` | 喜欢的类别或标签 |
| `dislikes` | `JSONB` | 不喜欢的类别或标签 |
| `budget_preference` | `TEXT` | 预算偏好 |
| `max_walking_minutes_per_segment` | `INTEGER` | 单段最大步行时间 |
| `explicit_preferences` | `JSONB` | 原始显式偏好 JSON |
| `created_at` | `TIMESTAMPTZ` | 创建时间 |
| `updated_at` | `TIMESTAMPTZ` | 更新时间 |

### `user_preference_weights`：用户偏好权重表

将用户学习偏好拆成键值权重，便于推荐模型直接读取、排序和更新。

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `user_id` | `TEXT` | 用户外键 |
| `preference_key` | `TEXT` | 偏好项，例如咖啡、安静、互动 |
| `weight` | `NUMERIC(6,3)` | 权重值 |
| `updated_at` | `TIMESTAMPTZ` | 更新时间 |

主键：

```text
(user_id, preference_key)
```

### `route_plans`：用户路线记录表

存储用户生成、保存或执行过的路线。当前生成数据不写入该表，后续由应用服务写入。

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `route_plan_id` | `UUID` | 路线主键，默认自动生成 |
| `user_id` | `TEXT` | 用户外键，可为空 |
| `title` | `TEXT` | 路线标题 |
| `status` | `TEXT` | 状态，例如 `draft`、`saved`、`completed` |
| `plan_date` | `DATE` | 计划日期 |
| `start_time` | `TIME` | 计划开始时间 |
| `total_distance_meters` | `INTEGER` | 总距离 |
| `total_duration_minutes` | `INTEGER` | 总耗时 |
| `total_budget` | `INTEGER` | 总预算 |
| `weather_context` | `JSONB` | 生成路线时的天气上下文 |
| `preference_snapshot` | `JSONB` | 生成路线时的用户偏好快照 |
| `created_at` | `TIMESTAMPTZ` | 创建时间 |
| `updated_at` | `TIMESTAMPTZ` | 更新时间 |

### `route_stops`：路线中的具体站点

存储某条路线中的 POI 顺序和停留计划。

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `route_stop_id` | `BIGSERIAL` | 自增主键 |
| `route_plan_id` | `UUID` | 路线外键 |
| `poi_id` | `TEXT` | POI 外键 |
| `stop_order` | `INTEGER` | 站点顺序 |
| `planned_arrival_at` | `TIMESTAMPTZ` | 计划到达时间 |
| `planned_departure_at` | `TIMESTAMPTZ` | 计划离开时间 |
| `stay_minutes` | `INTEGER` | 计划停留时长 |
| `note` | `TEXT` | 站点备注 |
| `created_at` | `TIMESTAMPTZ` | 创建时间 |

约束：

```text
(route_plan_id, stop_order) 唯一
```

### `feedback`：游后反馈表

存储用户对某个 POI 的自然语言反馈、标签补充和问题反馈。

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `feedback_id` | `TEXT` | 反馈主键 |
| `user_id` | `TEXT` | 用户 ID，当前不设外键 |
| `poi_id` | `TEXT` | POI 外键 |
| `sentiment` | `TEXT` | 情绪倾向，例如 positive、neutral、negative |
| `raw_feedback` | `TEXT` | 原始反馈文本 |
| `tags_added` | `JSONB` | 用户补充标签 |
| `issues` | `JSONB` | 用户反馈的问题 |
| `created_at` | `TIMESTAMPTZ` | 反馈时间 |

### `poi_feedback_summary`：POI 公共反馈聚合表

存储 POI 的聚合口碑，用于推荐排序和详情页展示。

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `poi_id` | `TEXT` | POI 外键，也是主键 |
| `feedback_count` | `INTEGER` | 反馈数量 |
| `positive_rate` | `NUMERIC(5,4)` | 正向反馈比例 |
| `common_praises` | `JSONB` | 常见优点 |
| `common_issues` | `JSONB` | 常见问题 |
| `tag_votes` | `JSONB` | 标签投票 |
| `photo_score_adjustment` | `NUMERIC(4,2)` | 拍照评分修正 |
| `conversation_score_adjustment` | `NUMERIC(4,2)` | 聊天评分修正 |
| `novelty_score_adjustment` | `NUMERIC(4,2)` | 新鲜感评分修正 |
| `relax_score_adjustment` | `NUMERIC(4,2)` | 放松评分修正 |
| `updated_at` | `TIMESTAMPTZ` | 更新时间 |

## 典型查询示例

查询附近 POI：

```sql
SELECT
    id,
    name,
    category,
    ROUND(
        ST_Distance(
            location,
            ST_SetSRID(ST_MakePoint(114.05, 22.55), 4326)::geography
        )
    )::INT AS distance_meters
FROM poi
ORDER BY location <-> ST_SetSRID(ST_MakePoint(114.05, 22.55), 4326)::geography
LIMIT 10;
```

查询适合地铁到达的 POI：

```sql
SELECT
    p.id,
    p.name,
    p.category,
    t.subway_station,
    t.subway_lines,
    t.subway_walk_minutes
FROM poi p
JOIN poi_transportation t ON t.poi_id = p.id
WHERE t.subway_recommended = TRUE
ORDER BY t.subway_walk_minutes;
```

查询某个 POI 可串联的下一个地点：

```sql
SELECT
    e.to_poi_id,
    p.name,
    p.category,
    e.distance_meters,
    e.walking_minutes,
    e.route_type
FROM route_edges e
JOIN poi p ON p.id = e.to_poi_id
WHERE e.from_poi_id = 'sz_poi_001'
ORDER BY e.distance_meters;
```

查询用户偏好权重：

```sql
SELECT preference_key, weight
FROM user_preference_weights
WHERE user_id = 'user_001'
ORDER BY weight DESC;
```

## 后续演进建议

如果要从 demo 数据升级到更真实的产品数据，建议按这个顺序演进：

1. 增加真实深圳地铁站表，字段包含站名、线路、经纬度。
2. 用 PostGIS 为每个 POI 计算真实最近地铁站，替换当前模拟地铁模板。
3. 增加真实行政区或商圈边界，用空间判断替换当前粗略区域划分。
4. 给 `feedback.user_id` 接入真实用户系统外键。
5. 将 `route_edges` 从直线距离升级为真实路网距离或地图 API 路线。
6. 给 `route_plans` 增加推荐分数、生成原因、用户修改记录等字段。
7. 将 POI 标签从 JSONB 演进为独立标签表，用于更复杂的统计和个性化推荐。
