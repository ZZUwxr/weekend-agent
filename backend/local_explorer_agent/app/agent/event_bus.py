from collections.abc import Callable

from local_explorer_agent.app.domain.models import PlanEvent


class EventBus:
    def __init__(self) -> None:
        self._subscribers: list[Callable[[PlanEvent], None]] = []

    def subscribe(self, handler: Callable[[PlanEvent], None]) -> None:
        self._subscribers.append(handler)

    def publish(self, event: PlanEvent) -> None:
        for handler in self._subscribers:
            handler(event)
