"""LLM client abstraction.

The whole project hinges on this clean swap point: MockLLMClient for local
iteration, VLLMClient pointing at Qwen2.5-72B on AMD MI300X for production.
Both implement the same async `complete` method returning structured JSON.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class LLMClient(ABC):
    """Async LLM client that returns parsed Pydantic models."""

    @abstractmethod
    async def complete(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        response_model: type[T],
        max_tokens: int = 4096,
        temperature: float = 0.1,
    ) -> T:
        """Run a chat completion and parse the response into `response_model`.

        Implementations must return a fully validated Pydantic instance.
        """
        ...
