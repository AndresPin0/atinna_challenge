"""
Modelos Pydantic para el servicio de resumen conversacional.
"""
from pydantic import BaseModel, Field
from typing import List, Optional


class MessageInput(BaseModel):
    """Modelo para un mensaje individual en la conversación."""
    id: str = Field(..., description="ID del mensaje")
    text: Optional[str] = Field(None, description="Texto del mensaje")
    createdAt: Optional[str] = Field(None, description="Timestamp de creación")
    author: Optional[str] = Field(None, description="Autor del mensaje")


class ResumenRequest(BaseModel):
    """Request para generar resumen de una conversación."""
    threadId: str = Field(..., description="ID del thread de conversación")
    messages: List[MessageInput] = Field(..., description="Lista de mensajes del thread")


class ResumenResponse(BaseModel):
    """Response con el resumen estructurado de la conversación."""
    threadId: str = Field(..., description="ID del thread analizado")
    resumen: str = Field(..., description="Resumen ejecutivo de la conversación")
    temas_clave: List[str] = Field(..., description="Lista de temas principales identificados")
    posturas: List[str] = Field(..., description="Posturas o posiciones detectadas en la conversación")
    tono_emocional: str = Field(..., description="Tono emocional predominante")
    riesgos_detectados: List[str] = Field(..., description="Riesgos o alertas identificadas")
    conclusion: str = Field(..., description="Conclusión del análisis")
    message_count: int = Field(..., description="Número de mensajes analizados")
