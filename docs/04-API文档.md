# API 文档

## 基础信息

- 基础路径：`/api/v1`
- 响应格式：JSON
- 认证方式：无（当前版本）
- CORS：允许所有来源

---

## 健康检查与元信息

### 健康检查

```
GET /api/v1/health
```

**响应**
```json
{
  "status": "ok",
  "app": "Weekend Agent",
  "env": "local"
}
```

### 数据健康检查

```
GET /api/v1/meta/data-health
```

**响应**
```json
{
  "data_dir": "/path/to/data",
  "overall_status": "ok",
  "files": {
    "poi": {
      "logical_name": "poi",
      "exists": true,
      "path": "/path/to/poi.json",
      "record_count": 150,
      "missing_required_fields": 0,
      "warnings": []
    }
  },
  "warnings": []
}
```

### 运行时元信息

```
GET /api/v1/meta/runtime
```

**响应**
```json
{
  "llm_provider": "openai",
  "llm_model": "qwen3.5-plus",
  "llm_base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
  "llm_allow_rule_based_fallback": false,
  "data_backend": "json",
  "database_url_set": false
}
```

### Schema 元信息

```
GET /api/v1/meta/schemas
```

返回所有枚举类型和渲染提示，前端可用于动态 UI 渲染。

---

## 规划接口

### 同步预览

```
POST /api/v1/plans/preview
```

**请求体** (`PlanPreviewRequest`)
```json
{
  "user_id": "u001",
  "query": "今天下午想和老婆孩子出去玩几小时，别太远，老婆最近在减肥，孩子5岁",
  "city": "深圳",
  "start_time": "2026-05-10T14:00:00",
  "duration_minutes": 240,
  "location": {
    "lat": 22.54,
    "lon": 114.05
  }
}
```

**字段说明**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| user_id | string | 是 | 用户 ID |
| query | string | 是 | 自然语言描述（1-2000 字符） |
| city | string | 否 | 城市，默认 "深圳" |
| start_time | datetime | 是 | 开始时间（ISO 8601） |
| duration_minutes | int | 是 | 持续时长（分钟，1-720） |
| location | object | 否 | 起始位置（经纬度） |

**响应** (`PlanOutput`)
```json
{
  "session_id": "sess_a1b2c3d4e5f6",
  "user_id": "u001",
  "created_at": "2026-05-10T14:00:00Z",
  "input_query": "今天下午想和老婆孩子出去玩几小时...",
  "inferred_context": {
    "group_type": "family",
    "roles": [
      {
        "role_id": "r1",
        "role_type": "adult_female",
        "display_name": "老婆",
        "hard_constraints": ["低卡饮食"],
        "soft_preferences": ["轻松活动"]
      },
      {
        "role_id": "r2",
        "role_type": "child",
        "display_name": "孩子",
        "hard_constraints": ["安全性高"],
        "soft_preferences": ["趣味性强"]
      }
    ],
    "group_size": 3,
    "scene_label": "family_afternoon"
  },
  "conflicts": [],
  "negotiation_strategies": [],
  "plan_candidates": [
    {
      "plan_id": "plan_a",
      "plan_type": "plan_a",
      "title": "轻松亲子下午",
      "theme": "亲子互动 + 轻运动",
      "stages": [],
      "timeline": [],
      "satisfaction_scores": [],
      "overall_score": 4.2,
      "min_role_score": 3.8,
      "fairness_score": 0.85
    }
  ],
  "recommended_plan_id": "plan_a",
  "execution_graph": [],
  "plan_version": 1,
  "state": "preview"
}
```

### 流式预览（SSE）

```
POST /api/v1/plans/preview/stream
```

请求体同同步预览。返回 `text/event-stream` 格式。

**SSE 事件类型**

| 事件 | 说明 |
|------|------|
| `step_start` | 步骤开始 |
| `step_complete` | 步骤完成 |
| `tool_call` | 工具调用 |
| `candidate_start` | 候选方案开始生成 |
| `candidate_complete` | 候选方案生成完成 |
| `plan_complete` | 规划完成 |
| `error` | 错误 |

**事件格式**
```
event: step_start
data: {"step": "user_understanding", "message": "正在理解用户意图..."}

event: step_complete
data: {"step": "user_understanding", "result": {...}}

event: plan_complete
data: {"session_id": "sess_a1b2c3d4e5f6", "recommended_plan_id": "plan_a"}
```

### 查询方案

```
GET /api/v1/plans/{session_id}
```

**路径参数**

| 参数 | 类型 | 说明 |
|------|------|------|
| session_id | string | 会话 ID |

**响应**：`PlanOutput`（同同步预览响应）

**错误码**
| 状态码 | 说明 |
|--------|------|
| 404 | 会话不存在 |

### 确认方案

```
POST /api/v1/plans/{session_id}/confirm
```

**路径参数**

| 参数 | 类型 | 说明 |
|------|------|------|
| session_id | string | 会话 ID |

**响应**：`PlanOutput`（状态变为 `confirmed`）

---

## 事件接口

### 触发事件（重规划）

```
POST /api/v1/plans/{session_id}/events
```

**路径参数**

| 参数 | 类型 | 说明 |
|------|------|------|
| session_id | string | 会话 ID |

**请求体** (`PlanEvent`)
```json
{
  "event_id": "evt_abc123",
  "session_id": "sess_a1b2c3d4e5f6",
  "event_type": "queue_change",
  "affected_poi_id": "poi_001",
  "severity": 3,
  "payload": {
    "new_wait_minutes": 45
  }
}
```

**事件类型** (`EventType`)
- `queue_change` - 排队状态变更
- `weather_change` - 天气变化
- `poi_closed` - POI 关闭
- `user_preference_change` - 用户偏好变更

**响应**：`PlanOutput`（重规划后的新方案）

**错误码**
| 状态码 | 说明 |
|--------|------|
| 400 | session_id 不匹配 |
| 404 | 会话不存在 |

---

## 执行接口

### 执行方案

```
POST /api/v1/plans/{session_id}/execute
```

**路径参数**

| 参数 | 类型 | 说明 |
|------|------|------|
| session_id | string | 会话 ID |

**响应** (`ExecutionResponse`)
```json
{
  "success": true,
  "tasks": [
    {
      "task_id": "task_001",
      "action": "book_restaurant",
      "poi_id": "poi_001",
      "status": "completed",
      "depends_on": [],
      "params": {"time": "18:00", "party_size": 3},
      "result": {"booking_id": "BK12345"},
      "mock_scenario": "success"
    },
    {
      "task_id": "task_002",
      "action": "call_taxi",
      "status": "completed",
      "depends_on": ["task_001"],
      "params": {"from": "poi_001", "to": "poi_002"},
      "result": {"taxi_id": "TX67890"}
    }
  ],
  "plan": { ... }
}
```

**执行动作** (`ExecutionAction`)
- `book_restaurant` - 预约餐厅
- `book_activity` - 预约活动
- `call_taxi` - 叫车
- `share_plan` - 分享方案

---

## 反馈接口

### 提交反馈

```
POST /api/v1/plans/{session_id}/feedback
```

**请求体** (`FeedbackRequest`)
```json
{
  "rating": 4,
  "raw_feedback": "方案整体不错，但第二个地点有点远",
  "tags": ["路线偏长", "POI 选择好"],
  "payload": {}
}
```

**字段说明**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| rating | int | 否 | 评分 1-5 |
| raw_feedback | string | 否 | 文本反馈（最多 2000 字符） |
| tags | list[string] | 否 | 标签 |
| payload | dict | 否 | 额外数据 |

**响应** (`FeedbackResponse`)
```json
{
  "success": true,
  "session_id": "sess_a1b2c3d4e5f6",
  "saved_feedback": {
    "rating": 4,
    "raw_feedback": "方案整体不错...",
    "tags": ["路线偏长", "POI 选择好"]
  }
}
```
