# Backend Endpoints Documentation

This document outlines all the backend endpoints required for the frontend application.

## Base URL
```
{BASE_URL}/api
```

## Endpoints

### 1. Travel Intent Analysis
**Endpoint:** `POST /travel/analyze-intent`

**Description:** Analyze user's travel intent based on their input message.

**Request Body:**
```json
{
  "message": "我和家人想在在今天下午出门放松放松",
  "userId": "string (optional)"
}
```

**Response:**
```json
{
  "status": "analyzing|conflict_detected|coordinating|solutions_ready",
  "message": "正在理解你的出行意图…",
  "data": {
    "intent": "string",
    "participants": []
  }
}
```

---

### 2. Get Travel Status
**Endpoint:** `GET /travel/status/:travelId`

**Description:** Retrieve the current status of a travel analysis.

**Response:**
```json
{
  "travelId": "string",
  "status": "analyzing|conflict_detected|coordinating|solutions_ready",
  "steps": [
    {
      "id": 1,
      "text": "正在理解你的出行意图…",
      "completed": true,
      "icon": "Loader2"
    },
    {
      "id": 2,
      "text": "检测到你们的需求有冲突…",
      "completed": false,
      "icon": "AlertCircle"
    },
    {
      "id": 3,
      "text": "正在协调你们的矛盾…",
      "completed": false,
      "icon": "ArrowLeftRight"
    },
    {
      "id": 4,
      "text": "有两个方案推荐给你…",
      "completed": false,
      "icon": "Lightbulb"
    }
  ]
}
```

---

### 3. Get User Needs
**Endpoint:** `GET /travel/:travelId/needs`

**Description:** Retrieve all participant needs for a travel plan.

**Response:**
```json
{
  "needs": [
    {
      "id": "string",
      "title": "5岁孩子",
      "icon": "baby",
      "description": [
        "需要儿童友好设施，指定清淡面食"
      ]
    },
    {
      "id": "string",
      "title": "老婆",
      "icon": "👩",
      "description": [
        "减脂期，低卡健康餐，偏好参与感强活动"
      ]
    }
  ]
}
```

---

### 4. Get Travel Solutions
**Endpoint:** `GET /travel/:travelId/solutions`

**Description:** Retrieve recommended solutions that balance all participants' needs.

**Response:**
```json
{
  "solutions": [
    {
      "id": "string",
      "title": "string",
      "description": "string",
      "activities": ["string"],
      "restaurants": ["string"],
      "matchScore": 0.95
    }
  ]
}
```

---

### 5. Save Travel Plan
**Endpoint:** `POST /travel/:travelId/save`

**Description:** Save a travel plan for future reference.

**Request Body:**
```json
{
  "title": "string",
  "selectedSolutionId": "string",
  "notes": "string (optional)"
}
```

**Response:**
```json
{
  "success": true,
  "planId": "string",
  "savedAt": "ISO 8601 timestamp"
}
```

---

### 6. Plan comparison (dual itinerary) — 第三屏 · 双方案对比
**Endpoint:** `GET /travel/:travelId/plan-comparison`

**与前端请求路径一致（`VITE_API_BASE_URL` + 下列 path）：**  
`GET /api/travel/:travelId/plan-comparison`

**Path parameters:**
| Name | Type | Description |
|------|------|-------------|
| `travelId` | string | 当前行程会话 id，与 `conversation-page` 相同 |

**Request body:** none

**Description:** Full payload for the Plan A / Plan B comparison screen (timeline, tags per activity, per-member scores, optional compensation copy).

**Frontend:** `fetchPlanComparisonPage` → `src/lib/api/plans.service.ts` · DTO `PlanComparisonPageDto` → `src/lib/api/types.ts`

**Response (shape mirrors `PlanComparisonPageDto` in frontend):**
```json
{
  "travelId": "string",
  "statusBarImageUrl": "string (URL)",
  "topStatusText": "准备为老婆和孩子安排行程……",
  "voiceInputIconUrl": "string (URL)",
  "assistantMessage": "好的，我基于你老婆、女儿的需求……",
  "plans": [
    {
      "id": "plan-a",
      "planLabel": "Plan A",
      "headline": "午后平衡 · 推荐",
      "recommended": true,
      "overallScoreLabel": "综合 3.62",
      "activities": [
        {
          "id": "a1",
          "title": "北京野生动物园",
          "durationLabel": "预计 2.5 h",
          "tags": [{ "id": "t1", "label": "体力 3.0/5" }]
        }
      ],
      "memberRatings": [
        {
          "id": "kid",
          "label": "孩子",
          "emoji": "👧",
          "score": 4.5,
          "starsFilled": 5
        }
      ],
      "compensationTitle": "补偿设计（情绪/成本）",
      "compensationParagraphs": ["optional bullet lines"]
    }
  ]
}
```

---

### 7. Itinerary timeline (detailed route) — 第四屏 · 时间轴＆路线
**Endpoint:** `GET /travel/:travelId/itinerary-timeline?planId=`

**与前端 `fetchItineraryTimelinePage` 请求路径一致：**  
`GET /api/travel/:travelId/itinerary-timeline?planId=plan-a`

**Description:** Returns the full-screen itinerary after the user confirms a plan (timeline rows, transport hints, footer summaries, status bar asset URLs). Same session `travelId` as other travel endpoints; `planId` should match a card `id` from `GET .../plan-comparison`.

**Query parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `planId` | string | yes | 与双方案页 `TravelPlanCardDto.id` 一致（如 `plan-a`、`plan-b`） |

**Path parameters:**
| Name | Type | Description |
|------|------|-------------|
| `travelId` | string | 行程会话 id（与 `POST /api/travel/sessions`、 `GET .../conversation-page` 相同） |

**Request body:** none

**Suggested HTTP errors:**
| Code | When |
|------|------|
| `400` | 缺少或非法的 `planId` |
| `404` | `travelId` 不存在，或该方案尚未生成时间轴 |

**Frontend:** `fetchItineraryTimelinePage` → `src/lib/api/itinerary.service.ts` · DTO `ItineraryTimelinePageDto` · Mock `src/lib/api/mock/timeline.mock.ts`

**Response (shape mirrors `ItineraryTimelinePageDto`; `detailLines` / `scheduleNote` / `transport` 均可按需省略):**
```json
{
  "travelId": "string",
  "planId": "plan-a",
  "statusBarImageUrl": "string",
  "voiceInputIconUrl": "string",
  "planPillLabel": "Plan A",
  "aiStatusMessage": "您已确认Plan A，正在生成Plan A 的详细时间轴＆路线…",
  "cardTitle": "时间轴＆路线…",
  "segments": [
    {
      "id": "seg-1",
      "scheduleLabel": "14:30",
      "scheduleNote": "出发",
      "title": "从家打车前往户外亲子农场",
      "metaLines": ["3km-约 12 分钟-预计 15 元"],
      "detailLines": ["可选：补充说明，多段则用数组多行展示"],
      "transport": { "emoji": "🚗", "label": "打车" }
    }
  ],
  "cardFooterSummary": "总时长：约 4 小时 10 分钟（14:30 - 18:40，含交通）",
  "pageFooterSummaryParts": {
    "highlight": "总时长：约 4 小时 10 分钟",
    "rest": "（14:30 - 18:40，含交通）"
  }
}
```

---

### 8. Booking todos (itinerary booking flow) — 第五屏 · 行程预约
**Endpoint:** `GET /travel/:travelId/booking-todos?planId=`

**与前端 `fetchBookingTodosPage` 请求路径一致：**  
`GET /api/travel/:travelId/booking-todos?planId=plan-a`

**Description:** Drives the conversational flow after the detailed timeline is shown: AI prompts, user confirmation pills, progress banner, and the **待办事项** card (venues, ride segments, status badges). The `flow` array is rendered **in order**; each element uses `type` to select UI (`ai_message` | `user_pill` | `progress_banner` | `todo_card`). Each `flow` item MUST include a unique `id` within the page payload (React list keys).

**Query parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `planId` | string | yes | 与双方案页 `TravelPlanCardDto.id` 一致（如 `plan-a`、`plan-b`） |

**Path parameters:**
| Name | Type | Description |
|------|------|-------------|
| `travelId` | string | 行程会话 id，与同会话其他 travel 接口一致 |

**Request body:** none

**Suggested HTTP errors:**
| Code | When |
|------|------|
| `400` | 缺少或非法的 `planId` |
| `404` | `travelId` 不存在，或尚未生成预约/待办内容 |

**Frontend:** `fetchBookingTodosPage` → `src/lib/api/booking-todos.service.ts` · DTOs `BookingTodosPageDto`, `BookingFlowItemDto`（`src/lib/api/types.ts`）· Mock `src/lib/api/mock/booking-todos.mock.ts`

**Response (abbreviated; see `BookingTodosPageDto` in `types.ts`):**
```json
{
  "travelId": "string",
  "planId": "plan-a",
  "statusBarImageUrl": "string",
  "voiceInputIconUrl": "string",
  "flow": [
    { "type": "ai_message", "id": "m1", "body": "已生成Plan A …" },
    { "type": "user_pill", "id": "u1", "label": "需要" },
    { "type": "progress_banner", "id": "p1", "body": "正在生成预约信息…" },
    {
      "type": "todo_card",
      "id": "td1",
      "card": {
        "title": "待办事项",
        "items": [
          {
            "id": "farm",
            "kind": "venue",
            "title": "户外亲子农场",
            "subtitle": "14:45 …",
            "thumbnailImageUrl": "string (optional)",
            "statusLabel": "待预约"
          },
          {
            "id": "rides",
            "kind": "rides",
            "title": "叫车安排",
            "lines": ["① …", "② …"],
            "statusLabel": "待预约"
          }
        ],
        "footerBannerText": "待预约"
      }
    }
  ]
}
```

---

### 9. Booking checkout (reservation summary & payment) — 第六屏 · 预约详情
**Endpoint:** `GET /travel/:travelId/booking-checkout?planId=`

**与前端 `fetchBookingCheckoutPage` 请求路径一致：**  
`GET /api/travel/:travelId/booking-checkout?planId=plan-a`

**Description:** After the booking flow (screen 5), returns structured venue cards (date/time/party/pricing or seating), a ride legs table, and payment prompt copy. Use the same `travelId` / `planId` as in §6–§8 for the session.

**Query / path parameters:** Same as §8 (`planId` required).

**Frontend:** `fetchBookingCheckoutPage` → `src/lib/api/booking-checkout.service.ts` · `BookingCheckoutPageDto` · Mock `src/lib/api/mock/booking-checkout.mock.ts`

**Response (abbreviated):**
```json
{
  "travelId": "string",
  "planId": "plan-a",
  "statusBarImageUrl": "string",
  "voiceInputIconUrl": "string",
  "topProgressText": "正在进行预约…",
  "venueCards": [
    {
      "id": "farm",
      "title": "户外亲子农场",
      "statusBadge": "已预约 · 待支付",
      "thumbnailImageUrl": "string",
      "rows": [{ "label": "日期", "value": "今天" }]
    }
  ],
  "rideCard": {
    "id": "rides",
    "title": "叫车安排",
    "statusBadge": "已安排 · 待支付",
    "legs": [
      {
        "id": "l1",
        "legIndex": "①",
        "categoryLabel": "时间",
        "route": "家 → 亲子农场",
        "distanceLabel": "3km",
        "durationLabel": "12-17min",
        "feeLabel": "¥15",
        "handlingLabel": "现在约好"
      }
    ],
    "tipText": "后面两段不用现在确定…"
  },
  "paymentPromptText": "是否确认支付"
}
```

---

### 10. Payment (checkout breakdown & methods) — 第七屏 · 付款
**Endpoint:** `GET /travel/:travelId/payment?planId=`

**与前端 `fetchPaymentPage` 请求路径一致：**  
`GET /api/travel/:travelId/payment?planId=plan-a`

**Description:** After the user confirms the reservation summary (screen 6), returns the payable line items, supported payment methods, and UX copy for the payment sheet. Use the same `travelId` / `planId` as in §6–§9. Ride legs: typically the **first** segment is included in the current payment; **later** segments may be `到时支付` until booked.

**Query / path parameters:** Same as §9 (`planId` required).

**Frontend:** `fetchPaymentPage` → `src/lib/api/payment.service.ts` · `PaymentPageDto` · Mock `src/lib/api/mock/payment.mock.ts`

**Response (abbreviated):**
```json
{
  "travelId": "string",
  "planId": "plan-a",
  "statusBarImageUrl": "string",
  "voiceInputIconUrl": "string",
  "topProgressText": "正在生成付款…",
  "breakdownTitle": "费用明细",
  "lineItems": [
    {
      "id": "farm",
      "itemLabel": "户外亲子农场",
      "detailText": "体验项目 1大1小 体验券 (2张)",
      "amountText": "¥88.00"
    }
  ],
  "paymentSectionTitle": "付款方式",
  "amountDueBadgeLabel": "本次需支付",
  "amountDueValue": "¥163",
  "paymentMethods": [
    {
      "id": "pm-wechat",
      "type": "wechat",
      "badgeText": "微",
      "label": "微信支付",
      "subtitle": "支持储蓄卡、信用卡等"
    }
  ],
  "defaultSelectedPaymentMethodId": "pm-wechat",
  "tapToPayHint": "请点击支付",
  "queryBannerText": "支付查询中…"
}
```

---

### 11. Trip live map (in-progress itinerary & map) — 第八屏 · 行程地图
**Endpoint:** `GET /travel/:travelId/trip-live-map?planId=`

**与前端 `fetchTripLiveMapPage` 请求路径一致：**  
`GET /api/travel/:travelId/trip-live-map?planId=plan-a`

**Description:** While the user is on the trip (after payment / confirmation), returns map imagery URLs and structured copy for the bottom sheet cards: itinerary snapshot (timeline + paid summary), current location vs next step, and scheduled reminders. Use the same `travelId` / `planId` as in earlier itinerary endpoints.

**Query / path parameters:** Same as §9 (`planId` required).

**Frontend:** `fetchTripLiveMapPage` → `src/lib/api/trip-live-map.service.ts` · `TripLiveMapPageDto` · Mock `src/lib/api/mock/trip-live-map.mock.ts`

**Response (abbreviated):**
```json
{
  "travelId": "string",
  "planId": "plan-a",
  "statusBarImageUrl": "string",
  "mapBackdropImageUrl": "string",
  "mapImageUrl": "string",
  "mapCornerImageUrl": "string",
  "snapshotCard": {
    "title": "行程快照",
    "timelineText": "14:30 🚗 出发 → …",
    "footerLeft": "全程约 4 小时",
    "footerEmphasis": "已支付 ¥183"
  },
  "locationCard": {
    "title": "当前位置与下一站",
    "currentLine": "当前：📍 户外亲子农场 · 剩余 45 分钟",
    "nextStepLine": "下一步：🕒 16:15 叫车前往素然花园"
  },
  "remindersCard": {
    "title": "内置提醒",
    "reminderLines": ["🔔 16:05 …", "🔔 18:35 …"]
  },
  "callRideButtonLabel": "叫车",
  "aiBubbleText": "请查看预约信息，是否确认预约",
  "voiceInputIconUrl": "string"
}
```

---

### 12. Payment confirmation (success & booking receipt) — 第九屏 · 支付确认
**Endpoint:** `GET /travel/:travelId/payment-confirmation?planId=`

**与前端 `fetchPaymentConfirmationPage` 请求路径一致：**  
`GET /api/travel/:travelId/payment-confirmation?planId=plan-a`

**Description:** Shown after successful payment: hero copy, booking confirmation table (items, details, status per row), paid total, optional upsell rows, horizontal itinerary chips, and post-booking helper actions. Reuse the same `travelId` / `planId` as §9–§11.

**Query / path parameters:** Same as §9 (`planId` required).

**Frontend:** `fetchPaymentConfirmationPage` → `src/lib/api/payment-confirmation.service.ts` · `PaymentConfirmationPageDto` · Mock `src/lib/api/mock/payment-confirmation.mock.ts`

**Response (abbreviated):**
```json
{
  "travelId": "string",
  "planId": "plan-a",
  "statusBarImageUrl": "string",
  "navTitle": "确认付款信息",
  "heroTitle": "支付成功!",
  "heroSubtitle": "下午的行程已全部就绪 ✨",
  "confirmationSectionTitle": "预订确认单",
  "tableColItem": "项目",
  "tableColDetail": "详情",
  "tableColStatus": "状态",
  "rows": [
    {
      "id": "r-farm",
      "itemLabel": "户外亲子农场",
      "detailText": "今天 14:45 · 3 人 · ¥168",
      "statusKind": "paid",
      "statusText": "已支付"
    }
  ],
  "totalLabel": "合计已支付",
  "totalValue": "¥183",
  "recommendedSectionTitle": "素然花园 · 推荐套餐…",
  "recommendedRows": [
    { "id": "rec-1", "name": "花园双人下午茶", "audienceLabel": "妻子", "priceText": "¥88", "thumbEmoji": "🍰" }
  ],
  "timelineSectionTitle": "行程速览",
  "timelineChips": [
    { "id": "t1", "time": "14:30", "iconEmoji": "🚗", "label": "出发" }
  ],
  "helpSectionTitle": "还能帮你",
  "helpActions": [
    { "id": "h1", "kind": "share", "label": "分享给家人" },
    { "id": "h2", "kind": "calendar", "label": "加入日历" },
    { "id": "h3", "kind": "bell", "label": "订阅行前提醒" }
  ],
  "helpSummaryText": "行前 30 分钟会提醒叫车…",
  "voiceInputIconUrl": "string"
}
```

---

### 13. Get User's Travel History
**Endpoint:** `GET /user/travels`

**Description:** Retrieve all saved travel plans for the current user.

**Response:**
```json
{
  "travels": [
    {
      "id": "string",
      "title": "string",
      "date": "ISO 8601 timestamp",
      "participants": ["string"],
      "status": "completed|in_progress|cancelled"
    }
  ]
}
```

---

### 14. Itinerary hub (current stage & history) — 第十屏 · 行程主页
**Endpoint:** `GET /travel/:travelId/itinerary-hub?planId=`

**与前端 `fetchItineraryHubPage` 请求路径一致：**  
`GET /api/travel/:travelId/itinerary-hub?planId=plan-a`

**Description:** Main **行程** tab: trip summary strip, vertical **当前阶段** timeline (`done` / `active` / `upcoming` nodes), five quick actions (`map` opens live map route; others are client-side until wired), and **历史行程** cards with rating and CTAs.

**Query / path parameters:** Same as §9 (`planId` required).

**Frontend:** `fetchItineraryHubPage` → `src/lib/api/itinerary-hub.service.ts` · `ItineraryHubPageDto` · Mock `src/lib/api/mock/itinerary-hub.mock.ts`

**Response (abbreviated):**
```json
{
  "travelId": "string",
  "planId": "plan-a",
  "statusBarImageUrl": "string",
  "navTitle": "行程",
  "showNotificationsBell": true,
  "overviewTimeRange": "今天下午 14:30 — 18:55",
  "overviewFlowChips": [{ "id": "f1", "iconEmoji": "🎯", "label": "农场" }],
  "overviewFooterLine": "约 4 小时 · 已付 ¥183",
  "currentStageTitle": "当前阶段",
  "currentStageStatusBadge": "进行中",
  "timelineNodes": [
    {
      "id": "t1",
      "kind": "done",
      "time": "14:30",
      "title": "已出发 / 叫车完成",
      "iconEmoji": "🚗"
    },
    {
      "id": "t3",
      "kind": "active",
      "time": "16:15",
      "title": "转场去素然花园",
      "subtitle": "16:05 提醒叫车",
      "iconEmoji": "🚕"
    }
  ],
  "quickActions": [
    { "id": "q1", "kind": "map", "label": "地图" },
    { "id": "q5", "kind": "cancel", "label": "取消" }
  ],
  "historySectionTitle": "历史行程",
  "historyItems": [
    {
      "id": "h1",
      "thumbEmoji": "🌾",
      "dateLine": "6 月 1 日",
      "routeSummary": "亲子农场 · 半日游",
      "ratingStars": 4,
      "priceText": "¥156"
    }
  ]
}
```

---

### 15. User profile (我的) — 第十一屏 · 个人主页
**Endpoint:** `GET /user/profile`

**与前端 `fetchProfilePage` 请求路径一致：**  
`GET /api/user/profile`

**Description:** 「我的」页：用户头像与默认起点、出行档案标签、出行偏好列表、记忆与偏好入口、常用出行模板及底栏快捷操作（分享/评价/帮助/关于）。与具体 `travelId` 解耦；客户端仍可在路由 `state` 中携带 `travelId` / `planId` 以驱动行程底栏导航。

**Frontend:** `fetchProfilePage` → `src/lib/api/profile.service.ts` · `ProfilePageDto` · Mock `src/lib/api/mock/profile.mock.ts`

**Response (abbreviated):**
```json
{
  "statusBarImageUrl": "string",
  "navTitle": "我的",
  "showNotificationsBell": true,
  "userName": "小明",
  "avatarEmoji": "👨‍💻",
  "defaultStartLine": "默认起点：家（科技生活区）",
  "archiveSectionTitle": "我的出行档案",
  "archiveEditLabel": "编辑",
  "archiveTags": [{ "id": "a1", "iconEmoji": "👶", "label": "儿子 · 5岁" }],
  "preferenceSectionTitle": "出行偏好",
  "preferenceEditLabel": "编辑",
  "preferenceRows": [
    {
      "id": "p1",
      "kind": "car",
      "title": "出行方式与距离",
      "summary": "打车 · 5km内 · 3–4小时"
    }
  ],
  "memorySectionTitle": "记忆与偏好",
  "memoryRows": [
    { "id": "m1", "kind": "agent_weights", "label": "Agent 学到的偏好权重" }
  ],
  "templatesSectionTitle": "常用出行模板",
  "templates": [
    { "id": "t1", "title": "周末家庭出行", "usageBadge": "使用 3 次", "thumbEmoji": "👨‍👩‍👧" }
  ],
  "quickFooterActions": [
    { "id": "q1", "kind": "share", "label": "分享" }
  ]
}
```

---

### 16. Travel mode & distance preferences — 第十二屏 · 出行方式与距离
**Endpoint:** `GET /user/preferences/travel-mode`

**与前端 `fetchTravelModeSettingsPage` 请求路径一致：**  
`GET /api/user/preferences/travel-mode`

**Description:** 子页：默认出行方式（单选）、默认半径（滑块 + 快捷公里 pill）、默认出行时长（单选），底部主按钮保存（前端当前仅回退至「我的」；持久化由 `PUT`/`PATCH` 后续对接）。

**Frontend:** `fetchTravelModeSettingsPage` → `src/lib/api/travel-mode-settings.service.ts` · `TravelModeSettingsPageDto` · Mock `src/lib/api/mock/travel-mode-settings.mock.ts`

**Response (abbreviated):**
```json
{
  "statusBarImageUrl": "string",
  "navTitle": "出行方式与距离",
  "backLabel": "返回",
  "methodSectionTitle": "默认出行方式",
  "methodOptions": [
    { "id": "taxi", "label": "打车" },
    { "id": "self_drive", "label": "自驾" },
    { "id": "transit", "label": "地铁/公交" }
  ],
  "selectedMethodId": "taxi",
  "radiusSectionTitle": "默认出行半径",
  "radiusValueFormat": "{km}km内",
  "radiusSliderMinKm": 1,
  "radiusSliderMaxKm": 15,
  "radiusSliderStepKm": 1,
  "selectedRadiusKm": 5,
  "radiusPresets": [
    { "id": "r3", "label": "3km", "valueKm": 3 },
    { "id": "r5", "label": "5km", "valueKm": 5 },
    { "id": "r10", "label": "10km", "valueKm": 10 }
  ],
  "durationSectionTitle": "默认出行时长",
  "durationOptions": [
    { "id": "dur-afternoon", "label": "3–4 小时（下午半天）" }
  ],
  "selectedDurationId": "dur-afternoon",
  "saveButtonLabel": "保存修改"
}
```

---

### 17. Dietary preferences — 第十三屏 · 饮食偏好
**Endpoint:** `GET /user/preferences/dietary`

**与前端 `fetchDietaryPreferencesPage` 请求路径一致：**  
`GET /api/user/preferences/dietary`

**Description:** 特殊饮食需求多选（可选 `exclusive` 与常规项互斥，如「无特殊」）；支持 `expandWhenChecked` 行前勾选后展示过敏源填写区；**添加人物偏好** 列表行可后续对接子路由。

**Frontend:** `fetchDietaryPreferencesPage` → `src/lib/api/dietary-preferences.service.ts` · `DietaryPreferencesPageDto` · Mock `src/lib/api/mock/dietary-preferences.mock.ts`

**Response (abbreviated):**
```json
{
  "statusBarImageUrl": "string",
  "navTitle": "饮食偏好",
  "navSubtitle": "适用对象：全部成员 / 可分别设置",
  "backLabel": "返回",
  "specialNeedsSectionTitle": "特殊饮食需求（可多选）",
  "needOptions": [
    { "id": "need-lowcal", "label": "低卡 / 健康轻食" },
    { "id": "need-none", "label": "无特殊", "exclusive": true },
    { "id": "need-allergen", "label": "过敏源（展开填写）", "expandWhenChecked": true }
  ],
  "selectedNeedIds": ["need-lowcal"],
  "familySectionTitle": "添加人物偏好",
  "familyMembers": [
    {
      "id": "f-son",
      "name": "儿子",
      "summaryLine": "偏好：儿童餐 · 不辣",
      "avatarEmoji": "👦"
    }
  ],
  "saveButtonLabel": "保存修改"
}
```

---

### 18. Activity preferences — 第十四屏 · 活动偏好（Figma 1:1301）
**Endpoint:** `GET /user/preferences/activity`

**与前端 `fetchActivityPreferencesPage` 请求路径一致：**  
`GET /api/user/preferences/activity`

**Description:** 活动类型多选标签 + **添加人物偏好** 家庭成员摘要列表（与饮食偏好页家庭成员行结构一致）；保存回「我的」由前端导航，持久化对接 `PUT`/`PATCH`。

**Frontend:** `fetchActivityPreferencesPage` → `src/lib/api/activity-preferences.service.ts` · `ActivityPreferencesPageDto` · Mock `src/lib/api/mock/activity-preferences.mock.ts`

**Response (abbreviated):**
```json
{
  "statusBarImageUrl": "string",
  "navTitle": "活动偏好",
  "backLabel": "返回",
  "tagsSectionTitle": "偏好的活动类型（可多选）",
  "tagOptions": [{ "id": "tag-nature", "label": "户外自然（公园/农场/绿道）" }],
  "selectedTagIds": ["tag-nature", "tag-interactive"],
  "familySectionTitle": "添加人物偏好",
  "familyMembers": [
    {
      "id": "f-son",
      "name": "儿子",
      "summaryLine": "体力充沛 · 需互动体验",
      "avatarEmoji": "👦"
    }
  ],
  "saveButtonLabel": "保存修改"
}
```

---

### 19. Budget & pace preferences — 第十五屏 · 预算与节奏（Figma 1:1302）
**Endpoint:** `GET /user/preferences/budget-pace`

**与前端 `fetchBudgetPacePreferencesPage` 请求路径一致：**  
`GET /api/user/preferences/budget-pace`

**Description:** 两个单选组：**预算倾向**（标题 + 说明 + 单选）与 **行程节奏偏好**（同上）；保存回「我的」由前端导航，持久化对接 `PUT`/`PATCH`。

**Frontend:** `fetchBudgetPacePreferencesPage` → `src/lib/api/budget-pace-preferences.service.ts` · `BudgetPacePreferencesPageDto` · Mock `src/lib/api/mock/budget-pace-preferences.mock.ts`

**Response (abbreviated):**
```json
{
  "statusBarImageUrl": "string",
  "navTitle": "预算与节奏",
  "backLabel": "返回",
  "budgetSectionTitle": "预算倾向",
  "budgetOptions": [
    {
      "id": "budget-medium",
      "title": "中等（人均80-150）",
      "description": "平衡预算与体验，兼顾性价比与舒适度。"
    }
  ],
  "selectedBudgetId": "budget-medium",
  "paceSectionTitle": "行程节奏偏好",
  "paceOptions": [
    {
      "id": "pace-relaxed",
      "title": "放松舒适（有缓冲休息）",
      "description": "留出充足休息时间，行程从容不赶路。"
    }
  ],
  "selectedPaceId": "pace-relaxed",
  "saveButtonLabel": "保存修改"
}
```

---

### 20. User preferences — PUT（保存四页偏好）

前端封装：`saveTravelModePreferences` · `saveDietaryPreferences` · `saveActivityPreferences` · `saveBudgetPacePreferences`（见各 `*-preferences.service.ts` / `travel-mode-settings.service.ts`）。  
未配置 `VITE_API_BASE_URL` 时前端**不请求**，本地视为保存成功以便开发。

| 方法 | 路径 | 请求体 TypeScript 类型 |
|------|------|------------------------|
| `PUT` | `/api/user/preferences/travel-mode` | `SaveTravelModePreferencesBody` |
| `PUT` | `/api/user/preferences/dietary` | `SaveDietaryPreferencesBody` |
| `PUT` | `/api/user/preferences/activity` | `SaveActivityPreferencesBody` |
| `PUT` | `/api/user/preferences/budget-pace` | `SaveBudgetPacePreferencesBody` |

**响应（建议）：** `UserPreferenceSaveResponseDto` — `{ "ok": true, "updatedAt": "ISO-8601" }`

**请求体示例（出行方式）：**
```json
{
  "selectedMethodId": "taxi",
  "selectedRadiusKm": 5,
  "selectedDurationId": "dur-afternoon"
}
```

**请求体示例（饮食）：**
```json
{
  "selectedNeedIds": ["need-lowcal", "need-allergen"],
  "allergenNote": "花生、海鲜"
}
```

---

### 21. Travel flow — POST/PATCH（预订 / 支付写操作）

前端封装：`src/lib/api/travel-flow-writes.service.ts` · `postBookingTodoAction` · `postBookingCheckoutConfirm` · `postTravelPaymentOrder` · `patchTravelPaymentOrderComplete`。  
页面可在用户点击「确认」「去支付」等时调用；未配置 base URL 时返回 mock 成功，不阻塞导航。

| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/api/travel/:travelId/booking-todos/actions` | 预约待办流中的操作；body：`BookingTodoActionBody`（`planId`, `itemId`, `action`, 可选 `metadata`） |
| `POST` | `/api/travel/:travelId/booking-checkout/confirm` | 预约核对页汇总确认；body：`TravelBookingCheckoutConfirmBody` |
| `POST` | `/api/travel/:travelId/payment/orders` | 创建支付单；body：`TravelPaymentSubmitBody`；响应可含 `paymentUrl` 跳转收银台 |
| `PATCH` | `/api/travel/:travelId/payment/orders/:orderId/complete?planId=` | 支付结果同步（轮询成功或回调后由前端或后端二选一发起的确认，按实际网关调整） |

实际 URL、鉴权与支付回调以网关为准；**保持请求/响应字段与 `types.ts` 中对齐**即可替换实现。

---

## Error Responses

All endpoints follow standard HTTP status codes:

- **200:** Success
- **400:** Bad Request (invalid input)
- **401:** Unauthorized (missing/invalid auth)
- **404:** Not Found (resource doesn't exist)
- **500:** Internal Server Error

**Error Response Format:**
```json
{
  "error": true,
  "message": "string",
  "code": "ERROR_CODE"
}
```

---

## Authentication

Include authentication token in request headers:
```
Authorization: Bearer {TOKEN}
```

---

## Notes for Backend Team

1. **Travel Status Flow:** The status progression follows: `analyzing` → `conflict_detected` → `coordinating` → `solutions_ready`

2. **Real-time Updates:** Consider implementing WebSocket or Server-Sent Events (SSE) for real-time status updates instead of polling.

3. **Icons:** The frontend uses lucide-react icons. Icon names referenced in responses should match the lucide-react icon library.

4. **Database Schema Considerations:**
   - Track user travel history
   - Store conflict detection results
   - Cache travel solutions
   - Maintain participant preferences

5. **Performance:** Consider caching frequently accessed solutions and travel plans.

6. **Plan comparison page:** Implement `GET /api/travel/:travelId/plan-comparison` so the client can replace mocks when `VITE_API_BASE_URL` is set. Response must match `PlanComparisonPageDto` (including optional `compensationTitle` / `compensationParagraphs` on a plan card).

7. **Itinerary timeline page:** Implement `GET /api/travel/:travelId/itinerary-timeline?planId=` returning `ItineraryTimelinePageDto`. The `planId` query should match `TravelPlanCardDto.id` from the plan-comparison response for that `travelId`. Return `404` if the timeline is not ready or the plan does not exist for the session.

8. **Booking todos page:** Implement `GET /api/travel/:travelId/booking-todos?planId=` returning `BookingTodosPageDto`. The `planId` must match a plan card id from plan-comparison for that `travelId`. Preserve the **ordered** `flow` array and unique `id` per item so the client renders copy and layout without hard-coding. If the user submits booking intent (e.g. taps 需要/确认), add separate `POST` endpoints later; this GET only supplies the current UI state.

9. **Booking checkout page:** Implement `GET /api/travel/:travelId/booking-checkout?planId=` returning `BookingCheckoutPageDto` (venue rows, ride leg table, tip text, payment prompt).

10. **Payment page:** Implement `GET /api/travel/:travelId/payment?planId=` returning `PaymentPageDto` (fee breakdown rows, payment method list, amount due badge, progress/hint strings). Actual charge / redirect / callback to WeChat Pay / Alipay / Meituan Pay should use your payment gateway; this GET only drives the seventh-screen UI state.

11. **Trip live map:** Implement `GET /api/travel/:travelId/trip-live-map?planId=` returning `TripLiveMapPageDto` (map image URLs, snapshot / location / reminders cards, AI bubble, call-ride label). Map tiles or static map URLs can be provider-specific; keep response shape stable for the client.

12. **Payment confirmation:** Implement `GET /api/travel/:travelId/payment-confirmation?planId=` returning `PaymentConfirmationPageDto` (hero strings, confirmation table rows with `statusKind` `paid` | `reserved` | `remind_later`, totals, recommended upsell rows, timeline chips, help actions with `kind` `share` | `calendar` | `bell`, summary copy). Optional `heroFigureImageUrl` for a decorative illustration.

13. **Itinerary hub:** Implement `GET /api/travel/:travelId/itinerary-hub?planId=` returning `ItineraryHubPageDto` (overview strip, timeline nodes with `kind` `done` | `active` | `upcoming`, quick action rows, history list). Align timeline state with booking/payment APIs for the same `planId`.

14. **User profile:** Implement `GET /api/user/profile` returning `ProfilePageDto` (user line, archive tags, preference rows with `kind` `car` | `food` | `activity` | `budget`, memory rows with `kind` `agent_weights` | `last_feedback` | `disliked_places`, templates, quick footer actions with `kind` `share` | `rate` | `help` | `about`). Authenticate per your app’s user session.

15. **Travel mode preferences:** Implement `GET /api/user/preferences/travel-mode` returning `TravelModeSettingsPageDto` (method options with `id` `taxi` | `self_drive` | `transit`, radius slider bounds and presets, duration option ids/labels). Add `PUT` or `PATCH` when the client submits **保存修改** to persist selections.

16. **Dietary preferences:** Implement `GET /api/user/preferences/dietary` returning `DietaryPreferencesPageDto` (`needOptions` with optional `exclusive` / `expandWhenChecked`, `selectedNeedIds`, `familyMembers` with `summaryLine`). Persist multi-select and allergen text on save via `PUT`/`PATCH` when wired.

17. **Activity preferences:** Implement `GET /api/user/preferences/activity` returning `ActivityPreferencesPageDto` (`tagOptions`, `selectedTagIds`, `familySectionTitle`, `familyMembers` — same row shape as dietary page). Optional `navSubtitle`. Add `PUT`/`PATCH` for **保存修改** when ready.

18. **Budget & pace preferences:** Implement `GET /api/user/preferences/budget-pace` returning `BudgetPacePreferencesPageDto` (`budgetOptions` / `selectedBudgetId`, `paceOptions` / `selectedPaceId`, each option has `title` + `description`). Add `PUT`/`PATCH` when the client submits **保存修改**.
