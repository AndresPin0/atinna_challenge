"""LangGraph definition for the conversational agent."""
from typing import Literal, TypedDict, Any, Optional, List, Dict
from langgraph.graph import StateGraph, END
from .nodes import AgentNodes
from .gemini import GeminiClient
from .memory import AgentState, ConversationMessage, AnalysisMemory


class GraphState(TypedDict):
    """Internal state for LangGraph (TypedDict for compatibility)."""
    user_query: str
    conversation_history: List[Dict[str, str]]
    last_analysis: Optional[Dict[str, Any]]
    current_thread_id: Optional[str]
    tool_decision: Optional[Dict[str, Any]]
    mcp_response: Optional[Dict[str, Any]]
    explanation: Optional[str]
    final_response: Optional[str]


def state_to_dict(state: AgentState) -> GraphState:
    """Convert Pydantic state to TypedDict for LangGraph."""
    return {
        "user_query": state.user_query,
        "conversation_history": [
            {"user": msg.user, "agent": msg.agent}
            for msg in state.conversation_history
        ],
        "last_analysis": state.last_analysis.model_dump() if state.last_analysis else None,
        "current_thread_id": state.current_thread_id,
        "tool_decision": state.tool_decision,
        "mcp_response": state.mcp_response,
        "explanation": state.explanation,
        "final_response": state.final_response
    }


def dict_to_state(state_dict: GraphState) -> AgentState:
    """Convert TypedDict back to Pydantic state."""
    state = AgentState(user_query=state_dict["user_query"])
    
    # Restore conversation history
    for msg in state_dict.get("conversation_history", []):
        state.add_message(user=msg["user"], agent=msg["agent"])
    
    # Restore last analysis
    if state_dict.get("last_analysis"):
        analysis = state_dict["last_analysis"]
        state.last_analysis = AnalysisMemory(**analysis)
    
    state.current_thread_id = state_dict.get("current_thread_id")
    state.tool_decision = state_dict.get("tool_decision")
    state.mcp_response = state_dict.get("mcp_response")
    state.explanation = state_dict.get("explanation")
    state.final_response = state_dict.get("final_response")
    
    return state


def create_agent_graph(gemini_client: GeminiClient):
    """
    Creates the LangGraph for the conversational agent.
    
    Args:
        gemini_client: Gemini client instance
        
    Returns:
        Compiled LangGraph
    """
    nodes = AgentNodes(gemini_client)
    
    # Wrapper functions to convert between Pydantic and TypedDict
    def decide_wrapper(state: GraphState) -> GraphState:
        pydantic_state = dict_to_state(state)
        result = nodes.decide_node(pydantic_state)
        state.update(result)
        return state
    
    def resumen_wrapper(state: GraphState) -> GraphState:
        pydantic_state = dict_to_state(state)
        result = nodes.resumen_node(pydantic_state)
        state.update(result)
        return state
    
    def explain_wrapper(state: GraphState) -> GraphState:
        pydantic_state = dict_to_state(state)
        result = nodes.explain_node(pydantic_state)
        state.update(result)
        return state
    
    def memory_wrapper(state: GraphState) -> GraphState:
        pydantic_state = dict_to_state(state)
        result = nodes.memory_node(pydantic_state)
        # Update state with saved analysis
        if pydantic_state.last_analysis:
            state["last_analysis"] = pydantic_state.last_analysis.model_dump()
        state.update(result)
        return state
    
    def respond_wrapper(state: GraphState) -> GraphState:
        pydantic_state = dict_to_state(state)
        result = nodes.respond_node(pydantic_state)
        # Update conversation history
        state["conversation_history"] = [
            {"user": msg.user, "agent": msg.agent}
            for msg in pydantic_state.conversation_history
        ]
        state.update(result)
        return state
    
    # Create graph
    graph = StateGraph(GraphState)
    
    # Add nodes
    graph.add_node("decide", decide_wrapper)
    graph.add_node("resumen", resumen_wrapper)
    graph.add_node("explain", explain_wrapper)
    graph.add_node("memory", memory_wrapper)
    graph.add_node("respond", respond_wrapper)
    
    # Set entry point
    graph.set_entry_point("decide")
    
    # Add edges from decide_node
    def should_call_tool(state: GraphState) -> Literal["resumen", "respond"]:
        """Conditional edge: decide if tool is needed."""
        tool_decision = state.get("tool_decision")
        if tool_decision and tool_decision.get("tool") == "mcp_resumen":
            return "resumen"
        return "respond"
    
    graph.add_conditional_edges(
        "decide",
        should_call_tool,
        {
            "resumen": "resumen",
            "respond": "respond"
        }
    )
    
    # Flow: resumen -> explain -> memory -> respond -> END
    graph.add_edge("resumen", "explain")
    graph.add_edge("explain", "memory")
    graph.add_edge("memory", "respond")
    graph.add_edge("respond", END)
    
    # Compile graph
    return graph.compile()

