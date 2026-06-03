# Mobile BFF API Contract

This document is the current frontend/backend contract for the Weekend Agent Android/Capacitor app.

## Base URL

Frontend `VITE_API_BASE_URL` must point to the mobile BFF root:

```env
VITE_API_BASE_URL=http://localhost:8000/api/v1/mobile
```

On Android emulator, the frontend maps `localhost` and `127.0.0.1` to `10.0.2.2`.

All mobile requests include an anonymous device user header:

```http
X-Device-User-Id: phone_<generated-id>
```

If the header is missing, the backend falls back to `phone_user`. The backend rejects invalid device ids with:

```json
{
  "code": "invalid_device_user_id",
  "message": "X-Device-User-Id 格式不合法。",
  "details": { "header": "X-Device-User-Id" }
}
```

## Runtime State

This round does not add login/register, SQLite/Postgres, or real payment/booking/taxi providers.

The backend uses JSON runtime persistence for:

- active travel
- plan sessions and agent state
- travel history
- user preferences
- feedback summaries
- provider action records

Runtime files live under `backend/local_explorer_agent/app/data/runtime/` and are ignored by git.

## Endpoints

All paths below are relative to `VITE_API_BASE_URL`.

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/travel/active` | Current device user's active travel |
| `POST` | `/travel/sessions` | Create a travel planning session |
| `POST` | `/travel/sessions/stream` | Create a session and stream agent progress by SSE |
| `GET` | `/travel/:travelId/conversation-page` | Conversation/clarification page |
| `POST` | `/travel/:travelId/clarifications` | Submit clarification answers |
| `GET` | `/travel/:travelId/plan-comparison` | Plan A/B comparison page |
| `POST` | `/travel/:travelId/revise` | Revise plan with natural language |
| `POST` | `/travel/:travelId/confirm` | Confirm selected plan |
| `GET` | `/travel/:travelId/itinerary-timeline?planId=` | Timeline route page |
| `GET` | `/travel/:travelId/booking-todos?planId=` | Booking todo page |
| `POST` | `/travel/:travelId/booking-todos/actions` | Record booking todo action |
| `GET` | `/travel/:travelId/booking-checkout?planId=` | Booking checkout page |
| `POST` | `/travel/:travelId/booking-checkout/confirm` | Record booking checkout confirmation |
| `GET` | `/travel/:travelId/payment?planId=` | Payment breakdown page |
| `POST` | `/travel/:travelId/payment/orders` | Create backend payment task record |
| `PATCH` | `/travel/:travelId/payment/orders/:orderId/complete?planId=` | Record payment confirmation attempt |
| `GET` | `/travel/:travelId/payment-confirmation?planId=` | Confirmation/receipt page |
| `GET` | `/travel/:travelId/trip-live-map?planId=` | Live map page |
| `POST` | `/travel/:travelId/execute` | Record provider-backed execution action |
| `GET` | `/travel/:travelId/itinerary-hub?planId=` | Itinerary hub page |
| `POST` | `/travel/:travelId/feedback` | Submit feedback and update memory/history |
| `GET` | `/home/dashboard` | Home dashboard with real history |
| `GET` | `/user/profile` | Profile with preference and feedback summaries |
| `GET`/`PUT` | `/user/preferences/travel-mode` | Travel mode preferences |
| `GET`/`PUT` | `/user/preferences/dietary` | Dietary preferences |
| `GET`/`PUT` | `/user/preferences/activity` | Activity preferences |
| `GET`/`PUT` | `/user/preferences/budget-pace` | Budget/pace preferences |

## Response Shapes

The canonical DTO definitions live in:

- frontend: `src/lib/api/types.ts`
- backend: `backend/local_explorer_agent/app/mobile/schemas.py`

Backend field aliases use camelCase for frontend responses.

## Provider Actions

Real provider integrations are not connected in this round. Booking, payment, taxi, navigation, calendar, reminder, and share actions must be recorded by the backend and returned as pending provider tasks, not faked as successful frontend operations.

Provider action responses use HTTP 200 with an unsuccessful business body:

```json
{
  "ok": false,
  "status": "pending_provider",
  "code": "provider_unavailable",
  "message": "外部服务暂未接入，已在后端记录为待处理任务。"
}
```

`POST /travel/:travelId/execute` accepts:

```json
{
  "planId": "plan-a",
  "action": "share_itinerary",
  "metadata": { "source": "itinerary_hub" }
}
```

Supported action labels include:

- `execute_plan`
- `share_itinerary`
- `calendar_reminder`
- `schedule_reminder`
- `call_ride`
- `navigation`
- `cancel_trip`

The frontend displays the backend `message` and may continue to the next app page for a complete runnable experience, but it must not present the provider action as a real third-party success.

## Errors

Errors use normalized JSON:

```json
{
  "code": "not_found",
  "message": "Plan session sess_xxx not found",
  "details": null
}
```

Expected status codes:

- `400`: invalid request or invalid device user id
- `404`: travel/session not found
- `409`: invalid state transition or conflict
- `422`: validation error
- `503`: provider/backend dependency unavailable

The frontend parses these with `ApiRequestError` in `src/lib/api/client.ts`.

## Authentication

There is no account auth in this round. Do not send `Authorization`; use `X-Device-User-Id` only.

## Android Runtime

Android debug installs automatically start the local backend via:

- `android/app/build.gradle`
- `scripts/start-backend.ps1`

The app expects the backend at `http://10.0.2.2:8000/api/v1/mobile` when running in the emulator.
