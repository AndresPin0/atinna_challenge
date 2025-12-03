"""Tool schemas and definitions for MCP services."""
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class MCPResumenRequest(BaseModel):
    """Request schema for MCP Resumen endpoint."""
    threadId: str = Field(description="Thread ID to analyze")


class MCPResumenResponse(BaseModel):
    """Response schema from MCP Resumen endpoint."""
    resumen: str = Field(description="Summary of the conversation")
    temas_clave: List[str] = Field(default_factory=list, description="Key themes")
    posturas: List[str] = Field(default_factory=list, description="Positions/stances")
    tono_emocional: str = Field(description="Emotional tone")
    riesgos_detectados: List[str] = Field(default_factory=list, description="Detected risks")
    conclusion: str = Field(description="Conclusion")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "resumen": self.resumen,
            "temas_clave": self.temas_clave,
            "posturas": self.posturas,
            "tono_emocional": self.tono_emocional,
            "riesgos_detectados": self.riesgos_detectados,
            "conclusion": self.conclusion
        }


class MCPSentimentRequest(BaseModel):
    """Request schema for MCP Sentiment endpoint."""
    threadId: Optional[str] = Field(
        default=None,
        description="Optional thread ID to analyze at sentiment level",
    )
    messageIds: Optional[List[str]] = Field(
        default=None,
        description="Optional list of message IDs to focus sentiment analysis on",
    )
    items: Optional[List[Dict[str, str]]] = Field(
        default=None,
        description=(
            "Optional list of items with 'id' and 'text' for direct sentiment analysis"
        ),
    )


class MCPPropagationRequest(BaseModel):
    """Request schema for MCP Propagation endpoint."""
    root_id: str = Field(description="Root message ID for propagation analysis")
    messages: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description=(
            "Optional list of messages that form the thread for propagation analysis"
        ),
    )


class ToolDefinition(BaseModel):
    """Definition of a tool available to the agent."""
    name: str = Field(description="Tool name")
    description: str = Field(description="Tool description")
    parameters: Dict[str, Any] = Field(description="Tool parameters schema")


AVAILABLE_TOOLS = {
    "mcp_resumen": ToolDefinition(
        name="mcp_resumen",
        description="Analiza una conversación y genera un resumen con temas clave, tono emocional, posturas y riesgos detectados",
        parameters={
            "type": "object",
            "properties": {
                "threadId": {
                    "type": "string",
                    "description": "ID del thread de conversación a analizar"
                }
            },
            "required": ["threadId"]
        }
    ),
    "mcp_sentiment": ToolDefinition(
        name="mcp_sentiment",
        description=(
            "Analiza el sentimiento y clima emocional de uno o varios mensajes "
            "de una conversación"
        ),
        parameters={
            "type": "object",
            "properties": {
                "threadId": {
                    "type": "string",
                    "description": "ID opcional del thread para análisis de sentimiento",
                },
                "messageIds": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": (
                        "IDs opcionales de mensajes específicos a analizar dentro del thread"
                    ),
                },
                "items": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                            "text": {"type": "string"},
                        },
                        "required": ["id", "text"],
                    },
                    "description": (
                        "Lista opcional de mensajes ya preparados para análisis "
                        "directo de sentimiento"
                    ),
                },
            },
            "required": [],
        },
    ),
    "mcp_propagation": ToolDefinition(
        name="mcp_propagation",
        description=(
            "Analiza la propagación, engagement y estructura de respuestas "
            "de un mensaje raíz en una conversación"
        ),
        parameters={
            "type": "object",
            "properties": {
                "root_id": {
                    "type": "string",
                    "description": "ID del mensaje raíz para analizar propagación",
                },
                "messages": {
                    "type": "array",
                    "items": {"type": "object"},
                    "description": (
                        "Lista opcional de mensajes que conforman el thread, "
                        "incluyendo información de autor, timestamps y relaciones"
                    ),
                },
            },
            "required": ["root_id"],
        },
    ),
}

