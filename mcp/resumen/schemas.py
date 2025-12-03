"""
Schemas de validación para el MCP de resumen conversacional.
"""
from pydantic import BaseModel, Field
from typing import List, Optional


class ResumenRequest(BaseModel):
    """Request schema para el endpoint de resumen."""
    threadId: str = Field(..., description="ID del thread de conversación")


class ResumenResponse(BaseModel):
    """Response schema con el resumen estructurado."""
    resumen: str = Field(..., description="Resumen ejecutivo de la conversación")
    temas_clave: List[str] = Field(..., description="Lista de temas principales identificados")
    posturas: List[str] = Field(..., description="Posturas o posiciones detectadas en la conversación")
    tono_emocional: str = Field(..., description="Tono emocional predominante")
    riesgos_detectados: List[str] = Field(..., description="Riesgos o alertas identificadas")
    conclusion: str = Field(..., description="Conclusión del análisis")


class ErrorResponse(BaseModel):
    """Schema para respuestas de error."""
    error: str = Field(..., description="Mensaje de error")
    detail: Optional[str] = Field(None, description="Detalle adicional del error")

