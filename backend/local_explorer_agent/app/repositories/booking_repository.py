from typing import Any

from local_explorer_agent.app.repositories.json_repository import JSONRepository


class BookingRepository(JSONRepository):
    filename = "booking_records.sample.json"

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._records: list[dict[str, Any]] | None = None

    def list_all(self) -> list[dict[str, Any]]:
        if self._records is None:
            self._records = list(self.load_json(self.filename))
        return self._records

    def add_record(self, record: dict[str, Any]) -> dict[str, Any]:
        self.list_all().append(record)
        return record
