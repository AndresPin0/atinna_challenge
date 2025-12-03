"""Memory management for the conversational agent."""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class ConversationMessage(BaseModel):
    """Single message in conversation history."""
    user: str = Field(description="User message")
    agent: str = Field(description="Agent response")
    timestamp: datetime = Field(default_factory=datetime.now)


class AnalysisMemory(BaseModel):
    """Stored analysis result."""
    thread_id: str = Field(description="Thread ID that was analyzed")
    resumen: str = Field(description="Summary text")
    tono_emocional: str = Field(description="Emotional tone")
    temas_clave: List[str] = Field(default_factory=list, description="Key themes")
    timestamp: datetime = Field(default_factory=datetime.now)


class AgentState(BaseModel):
    """State of the conversational agent."""
    user_query: str = Field(description="Current user query")
    conversation_history: List[ConversationMessage] = Field(
        default_factory=list,
        description="History of conversation"
    )
    last_analysis: Optional[AnalysisMemory] = Field(
        default=None,
        description="Last analysis performed"
    )
    current_thread_id: Optional[str] = Field(
        default=None,
        description="Current thread ID being discussed"
    )
    tool_decision: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Decision from router about which tool to use"
    )
    mcp_response: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Response from MCP service"
    )
    explanation: Optional[str] = Field(
        default=None,
        description="Natural language explanation of results"
    )
    final_response: Optional[str] = Field(
        default=None,
        description="Final response to user"
    )
    
    def add_message(self, user: str, agent: str) -> None:
        """Add a message to conversation history."""
        self.conversation_history.append(
            ConversationMessage(user=user, agent=agent)
        )
    
    def save_analysis(
        self, 
        thread_id: str, 
        resumen: str, 
        tono_emocional: str, 
        temas_clave: List[str]
    ) -> None:
        """Save analysis results to memory."""
        self.last_analysis = AnalysisMemory(
            thread_id=thread_id,
            resumen=resumen,
            tono_emocional=tono_emocional,
            temas_clave=temas_clave
        )
        self.current_thread_id = thread_id

