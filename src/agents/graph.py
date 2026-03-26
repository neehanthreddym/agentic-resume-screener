from langgraph.graph import StateGraph, END
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
    
    The workflow:
    1. Extract JD Skills & Extract Resume Skills (executed in parallel)
    2. Analyze Gaps (waits for both extractions)
    3. Generate Final Recommendation
    """
    # Sequential Flow: 
    # Start -> Extract JD -> Extract Resume -> Analyze Gaps -> Recommend -> End
    
    # 1. Initialize the graph with the ScreenerState schema
    builder = StateGraph(ScreenerState)
    
    # 2. Add the agent nodes
    builder.add_node("extract_jd", extract_jd_node)
    builder.add_node("extract_resume", extract_resume_node)
    builder.add_node("analyze_gaps", analyze_gaps_node)
    builder.add_node("generate_recommendation", generate_recommendation_node)
    
    # 3. Define the edges (workflow routing)
    # The entry point branches to both extraction nodes simultaneously
    builder.set_entry_point("extract_jd")
    builder.add_edge("extract_jd", "extract_resume")
    builder.add_edge("extract_resume", "analyze_gaps")
    builder.add_edge("analyze_gaps", "generate_recommendation")
    builder.add_edge("generate_recommendation", END)
        
    return builder.compile()

# Provide a pre-compiled global instance for easy import
screener_app = create_screener_graph()
