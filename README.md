# Weekend Agent

Weekend Agent 是一个用于周末地点推荐和路线规划的原型项目。

当前仓库包含：

- `data_process/generated_data.py`：从深圳坐标 CSV 生成 POI、路线边、用户画像和反馈示例数据。
- `data_process/Shenzhen.csv`：原始深圳坐标样本。
- `database/schema.sql`：PostgreSQL + PostGIS 表结构。
- `database/import_generated_data.py`：将生成 JSON 拆分导入数据库。
- `database/README.md`：完整数据库设计文档。

本地数据库运行数据、日志和生成 JSON 不提交到仓库，可按文档重新生成和导入。
