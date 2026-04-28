# Weekend Agent

Weekend Agent 是一个「本地探索 / 周末活动规划 Agent」后端原型。当前版本聚焦群体协商型活动规划：从自然语言里识别同行角色、硬约束、软偏好和内部冲突，再生成 Plan A / Plan B / 推荐方案、满意度评分、时间轴和 Mock 执行任务。

## 后端快速开始

```bash
conda activate weekend-agent
pip install -e .
python -m uvicorn local_explorer_agent.app.main:app --reload
```

服务启动后访问：

```bash
curl http://127.0.0.1:8000/api/v1/health
```

默认是 Mock LLM 模式：

```bash
LLM_PROVIDER=mock
```

## OpenAI-Compatible LLM

后端可以接入 OpenAI 官方 API 或 OpenAI-compatible 服务，但仍只使用本地虚拟数据。LLM 只负责结构化决策输出，POI、路线、排队、天气、用户画像仍来自 `DATA_DIR`，并通过 Tool / Repository 使用。

OpenAI 官方 API：

```bash
LLM_PROVIDER=openai
LLM_API_KEY=你的key
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4o-mini
LLM_API_STYLE=chat_completions
LLM_TRUST_ENV=false
```

兼容服务，例如本地 vLLM / OneAPI / LiteLLM：

```bash
LLM_PROVIDER=openai
LLM_API_KEY=你的兼容服务key
LLM_BASE_URL=http://localhost:8000/v1
LLM_MODEL=你的模型名
LLM_API_STYLE=chat_completions
LLM_TRUST_ENV=false
```

当前推荐使用 `chat_completions`，因为兼容生态更广；`responses` 已预留配置入口，但当前版本会自动降级到 rule-based fallback。

如果 `LLM_PROVIDER=openai` 但没有配置 `LLM_API_KEY`，服务启动不会崩溃；调用规划时会记录清晰错误并回退到 rule-based fallback。

## 本地虚拟数据

默认数据目录：

```bash
DATA_DIR=local_explorer_agent/app/data
```

Repository 会优先读取完整虚拟数据文件，例如 `poi.json`、`route_edges.json`，不存在时回退 `poi.sample.json`、`route_edges.sample.json`。如果你已经用 `data_process/generated_data.py` 生成了更完整的数据，可以把 `DATA_DIR` 指向对应目录：

```bash
DATA_DIR=data_process/generated_data
```

数据健康检查：

```bash
curl http://127.0.0.1:8000/api/v1/meta/data-health
```

该接口会返回每类数据文件是否存在、记录数量、缺失关键字段数量和 warning；少量字段缺失不会阻止服务运行。

## 生成规划示例

```bash
curl -X POST http://127.0.0.1:8000/api/v1/plans/preview \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "u001",
    "query": "今天下午想和老婆孩子出去玩几小时，别太远，老婆最近在减肥，孩子5岁",
    "city": "深圳",
    "start_time": "2026-05-10T14:00:00",
    "duration_minutes": 240,
    "location": {"lat": 22.54, "lon": 114.05}
  }'
```

## 测试和代码检查

```bash
pytest
ruff check .
```

## 当前架构

- `local_explorer_agent/app/api`：FastAPI 路由，只处理请求响应和依赖注入。
- `local_explorer_agent/app/services`：面向 API 的应用服务。
- `local_explorer_agent/app/agent`：轻量 Orchestrator、Skill、Prompt Runner、SessionStore。
- `local_explorer_agent/app/tools`：POI、路线、排队、天气、预订、叫车、分享等 Mock Tool。
- `local_explorer_agent/app/repositories`：本地 JSON Repository，后续可替换为 Redis / PostgreSQL / 外部服务。
- `local_explorer_agent/app/domain`：Pydantic v2 领域模型、枚举和评分逻辑。

## 现有数据资产

仓库仍保留原有数据生成和数据库原型：

- `data_process/generated_data.py`：从深圳坐标 CSV 生成 POI、路线边、用户画像和反馈示例数据。
- `data_process/Shenzhen.csv`：原始深圳坐标样本。
- `database/schema.sql`：PostgreSQL + PostGIS 表结构。
- `database/import_generated_data.py`：将生成 JSON 拆分导入数据库。
- `database/README.md`：完整数据库设计文档。

后端 v1 不直接依赖 ignored 的 `data_process/generated_data/*.json`，运行和测试使用 `local_explorer_agent/app/data/*.sample.json`。
