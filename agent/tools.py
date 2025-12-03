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
    )
}

