"""LangGraph orchestration for the PagerZero pipeline.

Day 1 shape (3 of 5 agents wired):

    START ──┬─► log_analysis ──────┐
            ├─► metrics_correlator ─┼─► END
            └─► deployment_tracker ─┘

LangGraph runs the three branches concurrently and waits for all of them
before terminating. Each node returns a partial state dict containing only
its own output field, so no reducers are needed.

Day 2 will replace `END` with the root_cause node (synthesizer) followed by
the remediation node.
"""

from __future__ import annotations

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from pagerzero.agents import (
    make_deployment_tracker_node,
    make_log_analysis_node,
    make_metrics_correlator_node,
)
from pagerzero.llm.client import LLMClient
from pagerzero.schemas import IncidentState


def build_graph(llm: LLMClient) -> CompiledStateGraph:
    """Compile the incident response graph with the given LLM client.

    Swap MockLLMClient for VLLMClient at deploy time — no other call site
    needs to change.
    """
    graph = StateGraph(IncidentState)

    graph.add_node("log_analysis", make_log_analysis_node(llm))
    graph.add_node("metrics_correlator", make_metrics_correlator_node(llm))
    graph.add_node("deployment_tracker", make_deployment_tracker_node(llm))

    # Fan out from START to all three agents in parallel.
    graph.add_edge(START, "log_analysis")
    graph.add_edge(START, "metrics_correlator")
    graph.add_edge(START, "deployment_tracker")

    # Day 1: each agent terminates the graph.
    # Day 2: replace these three edges with edges into `root_cause`.
    graph.add_edge("log_analysis", END)
    graph.add_edge("metrics_correlator", END)
    graph.add_edge("deployment_tracker", END)

    return graph.compile()
