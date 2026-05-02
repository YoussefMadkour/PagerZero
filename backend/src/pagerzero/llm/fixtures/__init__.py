"""Per-scenario canned Pydantic responses for MockLLMClient.

Adding a new scenario means: add a `scenario_<name>.py` module that exports
a `FIXTURES` dict, then register it in the FIXTURE_REGISTRY below.
"""

from __future__ import annotations

from collections.abc import Callable

from pydantic import BaseModel

from pagerzero.llm.fixtures import scenario_a, scenario_b, scenario_c

Fixture = Callable[[], BaseModel]

FIXTURE_REGISTRY: dict[str, dict[str, Fixture]] = {
    "scenario_a_memory_leak": scenario_a.FIXTURES,
    "scenario_b_pool_exhaust": scenario_b.FIXTURES,
    "scenario_c_cascade": scenario_c.FIXTURES,
}
