"""
Validation schemas for the Conversational Summary MCP.
"""
from pydantic import BaseModel, Field
from typing import List, Optional


class ResumenRequest(BaseModel):
    """Request schema for the summary endpoint."""
    threadId: str = Field(..., description="ID of the conversation thread")


class ResumenResponse(BaseModel):
    """Response schema with the structured summary."""
    resumen: str = Field(..., description="Resumen ejecutivo de la conversación")
    temas_clave: List[str] = Field(..., description="Lista de temas principales identificados")
    posturas: List[str] = Field(..., description="Posturas o posiciones detectadas en la conversación")
    tono_emocional: str = Field(..., description="Tono emocional predominante")
    riesgos_detectados: List[str] = Field(..., description="Riesgos o alertas identificadas")
    conclusion: str = Field(..., description="Conclusión del análisis")


class ErrorResponse(BaseModel):
    """Schema for error responses."""
    error: str = Field(..., description="Mensaje de error")
    detail: Optional[str] = Field(None, description="Detalle adicional del error")

