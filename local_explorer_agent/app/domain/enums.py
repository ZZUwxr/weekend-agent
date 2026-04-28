from enum import StrEnum


class RoleType(StrEnum):
    USER = "user"
    SPOUSE = "spouse"
    CHILD = "child"
    FRIEND = "friend"
    ELDER = "elder"
    UNKNOWN = "unknown"


class GroupType(StrEnum):
    FAMILY = "family"
    FRIENDS = "friends"
    COUPLE = "couple"
    SOLO = "solo"
    UNKNOWN = "unknown"


class ConflictType(StrEnum):
    ENERGY_MISMATCH = "energy_mismatch"
    DIET_CONFLICT = "diet_conflict"
    BUDGET_CONFLICT = "budget_conflict"
    PACE_CONFLICT = "pace_conflict"
    PHOTO_VS_PRACTICAL = "photo_vs_practical"
    INDOOR_OUTDOOR = "indoor_outdoor"
    UNKNOWN = "unknown"


class DecisionType(StrEnum):
    ACTIVITY = "activity"
    DINING = "dining"
    ROUTE = "route"
    TIMELINE = "timeline"


class StrategyType(StrEnum):
    ROTATE_PRIORITY = "rotate_priority"
    SOFTEN_CONFLICT = "soften_conflict"
    COMPENSATE_LOSER = "compensate_loser"
    MIN_REGRET = "min_regret"
    CONSTRAINT_FIRST = "constraint_first"


class StageType(StrEnum):
    ENERGY_RELEASE = "energy_release"
    EXPLORE = "explore"
    DINE = "dine"
    RELAX = "relax"
    TRANSPORT = "transport"
    BUFFER = "buffer"


class PlanType(StrEnum):
    PLAN_A = "plan_a"
    PLAN_B = "plan_b"
    RECOMMENDED = "recommended"


class TimelineItemType(StrEnum):
    ACTIVITY = "activity"
    TRANSPORT = "transport"
    DINING = "dining"
    BUFFER = "buffer"


class ExecutionAction(StrEnum):
    BOOK_RESTAURANT = "book_restaurant"
    BOOK_ACTIVITY = "book_activity"
    CALL_TAXI = "call_taxi"
    SHARE_PLAN = "share_plan"
    ORDER_GIFT = "order_gift"


class ExecutionStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    CONFIRMED = "confirmed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class PlanState(StrEnum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    EXECUTING = "executing"
    COMPLETED = "completed"
    REPLANNING = "replanning"
    FAILED = "failed"
    FEEDBACK = "feedback"


class EventType(StrEnum):
    QUEUE_OVERFLOW = "queue_overflow"
    WEATHER_CHANGE = "weather_change"
    USER_FEEDBACK = "user_feedback"
    BOOKING_FAILED = "booking_failed"
    TIME_OVERRUN = "time_overrun"
