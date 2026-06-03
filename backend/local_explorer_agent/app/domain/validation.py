"""Validation result models for plan constraint checking."""

from pydantic import BaseModel, Field


class PlanViolation(BaseModel):
    violation_type: str
    message: str
    severity: int = Field(ge=1, le=5)
    affected_plan_id: str | None = None
    affected_poi_id: str | None = None
    suggested_repair_action: str | None = None


class PlanValidationResult(BaseModel):
    passed: bool
    blocking_violations: list[PlanViolation] = Field(default_factory=list)
    warnings: list[PlanViolation] = Field(default_factory=list)
