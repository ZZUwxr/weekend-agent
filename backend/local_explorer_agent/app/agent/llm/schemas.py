from pydantic import BaseModel, Field

from local_explorer_agent.app.domain.models import Conflict, NegotiationStrategy, PlanCandidate


class ConflictListOutput(BaseModel):
    items: list[Conflict] = Field(default_factory=list)


class NegotiationStrategyListOutput(BaseModel):
    items: list[NegotiationStrategy] = Field(default_factory=list)


class PlanCandidateListOutput(BaseModel):
    items: list[PlanCandidate] = Field(default_factory=list)
