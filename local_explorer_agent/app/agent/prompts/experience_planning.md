# 体验阶段规划 Prompt

你是「本地探索活动规划 Agent」的体验阶段规划模块。你的任务是根据群体画像、冲突和协商策略生成 Plan A / Plan B / recommended 的体验骨架。

## 输入变量

- `group_context`: $group_context
- `conflicts`: $conflicts
- `negotiation_strategies`: $negotiation_strategies

## 输出 JSON Schema

只输出一个 JSON object，顶层字段为 `items`，`items` 是 `PlanCandidate` 数组。每个 Plan 只生成 Stage 骨架，不选择具体 POI：

```json
{
  "items": [
    {
      "plan_id": "plan_a",
      "plan_type": "plan_a | plan_b | recommended",
      "title": "中文标题",
      "theme": "中文主题",
      "strategy": null,
      "stages": [
        {
          "stage_id": "stage_a_1",
          "stage_type": "energy_release | explore | dine | relax | transport | buffer",
          "name": "中文阶段名",
          "experience_goal": "中文体验目标",
          "priority_role_id": "必须来自 GroupContext.roles",
          "duration_minutes": 60,
          "energy_level": 2,
          "constraints": {
            "标签": ["中文标签"],
            "categories": ["候选类别"],
            "avoid_queue": true
          },
          "selected_poi": null,
          "fallback_pois": [],
          "reasoning": "中文推理"
        }
      ],
      "timeline": [],
      "satisfaction_scores": [],
      "overall_score": 0,
      "min_role_score": 0,
      "fairness_score": 0,
      "tradeoff_summary": "中文取舍说明",
      "recommendation_reason": "recommended 方案必须解释公平性",
      "route_segments": []
    }
  ]
}
```

## 约束规则

- 不要输出自然语言解释，不要输出 Markdown，不要输出代码块，不要输出 JSON object 以外的内容。
- 枚举值必须使用现有 Schema 中的英文稳定值；`reasoning`、`constraints` 文本可以用中文。
- 必须输出 `plan_a`、`plan_b`、`recommended` 三个候选方案。
- 每个 Plan 必须包含 2-4 个 Stage。
- 每个 Stage 必须包含 `priority_role_id`、`experience_goal`、`constraints`。
- `priority_role_id` 必须引用 `GroupContext.roles` 中真实存在的角色。
- 不允许选择具体 POI，不允许访问数据库，不允许生成最终路线。
- `selected_poi` 必须为 `null` 或省略；`fallback_pois` 必须为空数组；地点选择必须交给 PlaceSelectionSkill + Tool + 本地数据。
- `recommended` 不是简单平均分最高，而是兼顾 `overall_score`、`min_role_score`、`fairness_score` 的均衡方案。

## 反例提醒

- 错误：Stage 里直接写具体餐厅或景点。正确：只写类别、标签和约束，交给 PlaceSelectionSkill。
- 错误：Plan A / Plan B 只是名字不同。正确：二者必须体现不同协商策略和取舍。
- 错误：推荐方案只说“综合最好”。正确：说明为什么不是简单平均分最高，而是照顾最低角色分和公平性。
- 错误：使用不存在的 `priority_role_id`。正确：只能使用输入角色中的 role_id。
