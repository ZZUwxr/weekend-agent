# Weekend Agent Planning 与 Memory 设计说明

本文说明 Weekend Agent 当前的规划策略、工具调用链路、异常处理机制，以及用户记忆与反馈评分写回机制。设计目标是让移动端用户用一句自然语言发起周末出行需求后，系统能结合本人偏好、同行人约束、POI/路线/天气/排队等本地事实，生成可解释、可校验、可继续修改的 Plan A / Plan B 与推荐方案。

## 1. Planning 策略

移动端入口是 `POST /api/v1/mobile/travel/sessions` 或 `/travel/sessions/stream`。BFF 会先把用户输入转成 `PlanPreviewRequest`：从文本中轻量推断城市、开始时间、出行时长，并读取 `X-Device-User-Id` 作为匿名用户 ID；如果用户选择同行人，则把 companion ids 一并带入。随后 `PlanService` 调用默认的 ReAct runtime。移动端请求也可携带本地 LLM 配置；如果配置不完整或未启用 OpenAI-compatible provider，则走 Mock Decider，保证 demo 链路可离线跑通。

核心规划循环是“状态驱动”的 ReAct：`Decider -> Policy -> Executor -> Reducer`。Decider 根据当前 `AgentState` 和工具列表选择下一步动作；Policy 检查动作是否满足前置条件和安全边界；Executor 调用具体工具；Reducer 把 observation 合并回状态。循环直到状态进入 `completed`、`failed` 或 `needs_user_input`。

策略上系统不是直接让模型一次性输出完整行程，而是把规划拆成可控阶段：

1. 先读用户记忆与同行人档案，形成 personalization context。
2. 再做需求采集，识别活动数量、硬约束、缺失 slot 与澄清问题。
3. 若缺失信息可以用安全默认假设补齐，则继续规划；若必须确认，则返回澄清态。
4. 生成群体理解、冲突检测与协商策略，明确不同成员之间的取舍。
5. 生成候选体验结构，再调用事实工具选 POI、算路线、构建时间轴。
6. 进入约束校验与修复，最后打分并选择推荐方案。

Policy 是规划质量的“硬门”。它强制 `read_user_memory` 和 `intake_user_requirements` 必须早于核心规划；`detect_conflicts` 必须早于方案生成之后的步骤；如果存在冲突，必须先生成协商策略；最终输出前必须完成地点选择、路线计算、时间轴、约束校验和评分。Preview 阶段禁止真实执行类工具，只允许生成待确认任务，避免误下单、误叫车或误分享。

## 2. 工具调用链路

当前 ReAct runtime 的工具注册集中在 `agent/react/factory.py`，可分为五类：

- Memory 工具：`read_user_memory` 读取本人偏好、同行人约束、历史反馈权重。
- 理解与规划工具：`intake_user_requirements`、`understand_user`、`detect_conflicts`、`generate_negotiation_strategy`、`draft_experience_plan`。
- 事实工具：`poi_search`、`poi_detail`、`route_search`、`weather_lookup`、`queue_lookup`，全部基于本地 JSON repository。
- 生成与校验工具：`select_places`、`calculate_routes`、`build_timeline`、`validate_plan_constraints`、`repair_plan`、`score_candidates`。
- 修改与准备工具：`interpret_revision_request`、`replace_poi`、`revise_dining_stage`、`add_followup_stage`、`rebuild_timeline`、`booking_prepare`、`taxi_prepare`、`share_prepare`。

一条典型链路如下：

`read_user_memory -> intake_user_requirements -> clarify_requirements -> understand_user -> detect_conflicts -> generate_negotiation_strategy -> draft_experience_plan -> select_places -> calculate_routes -> build_timeline -> validate_plan_constraints -> repair_plan(可选) -> score_candidates -> final_answer`

输出的 `PlanOutput` 不直接暴露给前端页面。Mobile BFF 通过 `mobile/presenter.py` 把同一份领域模型投影成页面级 DTO，例如方案对比页、时间轴页、预约待办页、支付预览页、行程中地图页和行程主页。这样业务规划只维护一套领域模型，前端页面可以稳定消费面向 UI 的数据结构。

## 3. Memory 设计

Memory 是本项目个性化能力的核心，当前以本地 JSON 文件实现，路径位于数据目录下的 `user_memory/{safe_user_id}.json`。Repository 会对 user id 和 companion id 做路径安全清洗，并使用临时文件加 `os.replace` 原子写入，避免半写入破坏记忆文件。

用户记忆由四部分组成：

- `profile`：默认城市、默认时长、预算偏好、节奏偏好、单段最大步行时间等稳定偏好。
- `companions`：同行人档案，包括角色、年龄、硬约束、软偏好和风险点。默认会初始化“老婆减脂期”和“5 岁儿子”两个典型同行人。
- `preferences`：可学习偏好，包括 likes/dislikes、category_weights、tag_weights、liked_poi_ids、disliked_poi_ids。
- `feedback_history`：最近 50 条用户反馈，用于审计和后续个性化。

规划开始时，`read_user_memory` 会把完整记忆压缩成 `UserMemoryContext`。这个 context 一方面进入 LLM/Mock 决策摘要，另一方面影响地点选择和最终说明。系统遵循“当前输入优先于历史记忆”的规则：如果用户本次明确说“想吃烧烤”，即使记忆里有低卡偏好，也不会直接否定，而是在校验和推荐理由中提示高热量冲突与补偿策略。

Memory 也支持同行人选择。移动端首页可以传入 companion ids，后端只把选中的同行人放入 `selected_companion_ids` 与 planning context。这样“本人独处”“带孩子”“情侣约会”不会混用同一组约束。

## 4. 用户评分写回本人记忆

行程结束后，移动端通过反馈接口提交评分、标签、自然语言反馈和可选 payload。`FeedbackService.submit_feedback` 会先保存 feedback record，再调用 `MemoryUpdateService.apply_feedback` 写回本人记忆，并把 plan state 更新为 `FEEDBACK`。

写回规则是轻量、可解释的：

- 评分 `>=4` 视为正反馈，对推荐方案中实际选中的 POI 类别和标签增加权重 `+0.1`。
- 评分 `<=2` 视为负反馈，对相关类别和标签降低权重 `-0.15`。
- 评分为 `3` 或未评分时，仅追加反馈历史，不改偏好权重。
- 权重被限制在 `[0.5, 1.8]`，避免一次极端反馈把后续推荐完全带偏。
- 如果 payload 明确传入 `liked_categories`、`disliked_categories`、`liked_poi_ids` 或 `disliked_poi_ids`，优先使用显式反馈；否则从推荐方案 POI 和自然语言关键词中提取类别/标签。

例如用户给推荐方案 5 分，且推荐方案包含“公园 + 轻食 + 亲子互动”，系统会提高这些 category/tag 的权重，并把对应 POI 加入 `liked_poi_ids`。下一次规划时，`read_user_memory` 会把这些偏好带入 context，使 Agent 更倾向选择相似体验。相反，如果用户低分并说“排队太久、太吵”，系统会降低“排队/热闹”等相关标签的权重，并记录不喜欢的 POI。

## 5. 异常处理机制

异常处理分三层：

第一层是输入与资源错误。FastAPI 统一把参数校验错误返回为 `validation_error`，找不到 session 或 agent state 时返回 `not_found`。移动端设备 ID 会做格式校验，避免路径穿越或异常文件名进入 memory/runtime 存储。

第二层是 LLM 与结构化输出错误。`JSONPromptRunner` 会尝试按 Pydantic schema 解析模型输出；如果模型失败且允许规则兜底，则调用 fallback，继续产出可运行 demo。OpenAI-compatible 调用失败会被归类为 `llm_rate_limited`、`llm_timeout`、`llm_invalid_response` 或 `llm_unavailable`，同时对错误文本中的 API key、Authorization、Bearer token 做脱敏。

第三层是规划过程错误。Policy 会阻止越权动作、跳步动作和 preview 阶段执行工具。Runtime 会在 action 违反策略时尝试自动纠偏，例如补读 memory、补做需求采集、补做校验或改为修复动作。最终输出前的 validator 会检查城市不匹配、儿童安全、营业时间、缺路线、时长超限、距离过远、天气和排队风险等问题；严重违规会进入 `repair_plan`，最多按配置修复若干次。若仍存在阻塞性问题，则返回失败或澄清态，而不是输出不可执行方案。
