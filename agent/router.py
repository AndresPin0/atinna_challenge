"""Router logic for tool decision making."""
from typing import Dict, Any, Optional
from .gemini import GeminiClient
from .memory import AgentState


class Router:
    """Routes user queries to appropriate tools."""
    
    def __init__(self, gemini_client: GeminiClient):
        """
        Initialize router.
        
        Args:
            gemini_client: Gemini client instance
        """
        self.gemini_client = gemini_client
    
    def decide(
        self, 
        state: AgentState
    ) -> Dict[str, Any]:
        """
        Decides which tool to use based on user query.
        
        Args:
            state: Current agent state
            
        Returns:
            Decision dict with 'tool', 'arguments', and 'response' keys
        """
        # Prepare conversation history
        history = None
        if state.conversation_history:
            history = [
                {"user": msg.user, "agent": msg.agent}
                for msg in state.conversation_history[-5:]
            ]
        
        # Get available threadId from state
        available_thread_id = state.current_thread_id
        if state.last_analysis:
            available_thread_id = state.last_analysis.thread_id
        
        # Get decision from Gemini
        decision = self.gemini_client.decide_tool(
            user_query=state.user_query,
            conversation_history=history,
            available_thread_id=available_thread_id
        )
        
        # Validate decision structure
        if not isinstance(decision, dict):
            raise ValueError(f"Invalid decision format: {decision}")
        
        if "tool" not in decision:
            raise ValueError("Decision missing 'tool' key")
        
        # Validate tool name if provided
        allowed_tools = ["mcp_resumen", "mcp_sentiment", "mcp_propagation", None]
        if decision["tool"] not in allowed_tools:
            raise ValueError(f"Unknown tool: {decision['tool']}")
        
        # Validate / enrich arguments if tool is provided
        tool_name = decision["tool"]

        # mcp_resumen: ensure threadId is present, inherit from context if needed
        if tool_name == "mcp_resumen":
            if not decision.get("arguments") or not decision["arguments"].get("threadId"):
                # Try to use available threadId from state
                if available_thread_id:
                    if not decision.get("arguments"):
                        decision["arguments"] = {}
                    decision["arguments"]["threadId"] = available_thread_id
                else:
                    raise ValueError("mcp_resumen requires 'threadId' in arguments or in conversation context")

        # mcp_sentiment: try to supply threadId from context if needed
        if tool_name == "mcp_sentiment":
            args = decision.get("arguments") or {}
            if "threadId" not in args and available_thread_id:
                args["threadId"] = available_thread_id
            decision["arguments"] = args

        # mcp_propagation: requires at least root_id in arguments
        if tool_name == "mcp_propagation":
            args = decision.get("arguments") or {}
            if "root_id" not in args:
                raise ValueError("mcp_propagation requires 'root_id' in arguments")
            decision["arguments"] = args
        
        return decision

