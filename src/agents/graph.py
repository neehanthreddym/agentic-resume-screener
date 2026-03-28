from langgraph.graph import StateGraph, END, START

from src.schemas.models import ScreenerState
from src.agents.nodes import (
    extract_jd_node,
    extract_resume_node,
    analyze_gaps_node,
    generate_recommendation_node
)


def create_screener_graph() -> StateGraph:
    """
    Constructs and compiles the LangGraph pipeline for the Resume Screener.

    Workflow (async parallel fan-out):
      START ──► extract_jd (async) ──┐
            └──► extract_resume (async) ─┤
                                         ▼
                                    analyze_gaps ─► generate_recommendation ─► END

    Both extraction nodes are async and run concurrently. LangGraph waits
    for both to complete before executing analyze_gaps.
    Use `await screener_app.ainvoke(state)` in notebooks and APIs.
    """
    builder = StateGraph(ScreenerState)

    # Add nodes
    builder.add_node("extract_jd", extract_jd_node)
    builder.add_node("extract_resume", extract_resume_node)
    builder.add_node("analyze_gaps", analyze_gaps_node)
    builder.add_node("generate_recommendation", generate_recommendation_node)

    # Fan-out: START branches to both extraction nodes in parallel
    builder.add_edge(START, "extract_jd")
    builder.add_edge(START, "extract_resume")

    # Fan-in: both extraction nodes converge at analyze_gaps
    builder.add_edge("extract_jd", "analyze_gaps")
    builder.add_edge("extract_resume", "analyze_gaps")

    # Sequential tail
    builder.add_edge("analyze_gaps", "generate_recommendation")
    builder.add_edge("generate_recommendation", END)

    return builder.compile()


# Pre-compiled global instance for easy import
screener_app = create_screener_graph()