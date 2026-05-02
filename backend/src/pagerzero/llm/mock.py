"""MockLLMClient — returns canned, scenario-specific Pydantic responses.

Lets the full LangGraph pipeline + FastAPI + Next.js dashboard run on a
laptop in seconds with zero AMD credit burn. Real Qwen via VLLMClient swaps
in only at the deployment boundary.

Per-scenario fixtures live in `pagerzero.llm.fixtures` — adding a new
scenario means dropping a `scenario_<name>.py` file there and registering
its FIXTURES dict in `fixtures/__init__.py`.
"""

from __future__ import annotations

import asyncio
from typing import TypeVar

from pydantic import BaseModel

from pagerzero.llm.client import LLMClient
from pagerzero.llm.fixtures import FIXTURE_REGISTRY

T = TypeVar("T", bound=BaseModel)


class MockLLMClient(LLMClient):
    """Returns canned Pydantic responses keyed by scenario + response model.

    The simulated latency makes the SSE streaming demo show agents lighting
    up in real time rather than instantly.
    """

    def __init__(
        self,
        scenario: str = "scenario_a_memory_leak",
        simulated_latency_seconds: float = 0.4,
    ) -> None:
        self.scenario = scenario
        self.simulated_latency_seconds = simulated_latency_seconds

    async def complete(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        response_model: type[T],
        max_tokens: int = 4096,
        temperature: float = 0.1,
    ) -> T:
        await asyncio.sleep(self.simulated_latency_seconds)

        fixtures = FIXTURE_REGISTRY.get(self.scenario)
        if fixtures is None:
            raise ValueError(f"No mock fixtures for scenario {self.scenario!r}")

        fixture = fixtures.get(response_model.__name__)
        if fixture is None:
            raise ValueError(
                f"No mock fixture for {response_model.__name__} in {self.scenario!r}"
            )

        result = fixture()
        if not isinstance(result, response_model):
            raise TypeError(
                f"Fixture for {response_model.__name__} returned "
                f"{type(result).__name__}"
            )
        return result
