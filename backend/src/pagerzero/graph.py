"""LangGraph orchestration for the full PagerZero pipeline.

    START ──┬─► log_analysis ──────┐
            ├─► metrics_correlator ─┼─► root_cause ──► remediation ──► END
            └─► deployment_tracker ─┘

LangGraph runs the three branches concurrently from START, then waits for
all of them to complete before transitioning into root_cause (because
root_cause has three incoming edges). Remediation runs sequentially after
root_cause.

Each parallel agent writes to its own state field, so no reducers are
needed. The synthesizer agents (root_cause, remediation) read the populated
fields from prior nodes — see the asserts inside each node module.
"""

from __future__ import annotations

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from pagerzero.agents import (
    make_deployment_tracker_node,
    make_log_analysis_node,
    make_metrics_correlator_node,
    make_remediation_node,
    make_root_cause_node,
)
from pagerzero.llm.client import LLMClient
from pagerzero.schemas import IncidentState

PARALLEL_AGENTS: tuple[str, ...] = (
    "log_analysis",
    "metrics_correlator",
    "deployment_tracker",
)
SYNTHESIZER_AGENTS: tuple[str, ...] = ("root_cause", "remediation")
ALL_AGENTS: tuple[str, ...] = PARALLEL_AGENTS + SYNTHESIZER_AGENTS


def build_graph(llm: LLMClient) -> CompiledStateGraph:
    """Compile the incident response graph with the given LLM client.

    Swap MockLLMClient for VLLMClient at deploy time — only this call site
    changes.
    """
    graph = StateGraph(IncidentState)

    graph.add_node("log_analysis", make_log_analysis_node(llm))
    graph.add_node("metrics_correlator", make_metrics_correlator_node(llm))
    graph.add_node("deployment_tracker", make_deployment_tracker_node(llm))
    graph.add_node("root_cause", make_root_cause_node(llm))
    graph.add_node("remediation", make_remediation_node(llm))

    # Fan out from START to all three specialists in parallel.
    for agent in PARALLEL_AGENTS:
        graph.add_edge(START, agent)

    # All three converge into root_cause; LangGraph waits for all of them
    # before firing root_cause exactly once.
    for agent in PARALLEL_AGENTS:
        graph.add_edge(agent, "root_cause")

    graph.add_edge("root_cause", "remediation")
    graph.add_edge("remediation", END)

    return graph.compile()
