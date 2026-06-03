from typing import Protocol, TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class BaseLLMClient(Protocol):
    def complete_json(self, prompt: str, schema: type[T]) -> T:
        """Complete a prompt and validate the JSON result with a Pydantic schema."""
