from datetime import datetime

from pydantic import BaseModel

from local_explorer_agent.app.domain.schemas import Location


class PlanningContext(BaseModel):
    user_id: str
    query: str
    city: str
    start_time: datetime
    duration_minutes: int
    location: Location | None = None
