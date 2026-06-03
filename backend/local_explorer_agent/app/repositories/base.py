from typing import Any, Protocol


class Repository(Protocol):
    def list_all(self) -> list[Any]:
        """Return all repository records."""
