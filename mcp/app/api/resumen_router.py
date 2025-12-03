"""
Router para el endpoint de resumen conversacional.
"""
from fastapi import APIRouter, HTTPException
from typing import Dict

from app.models.resumen_models import ResumenRequest, ResumenResponse
from app.services.resumen_service import ResumenService

router = APIRouter(
    prefix="/api/v1/analysis",
    tags=["resumen"]
)

# Instancia del servicio (singleton)
resumen_service = ResumenService()


@router.post("/resumen", response_model=ResumenResponse)
async def generar_resumen(request: ResumenRequest) -> ResumenResponse:
    """
    Genera un resumen ejecutivo de una conversación.
    
    Args:
        request: ResumenRequest con threadId y lista de mensajes
        
    Returns:
        ResumenResponse con el análisis estructurado
        
    Raises:
        HTTPException: Si hay error en el procesamiento
    """
    try:
        resultado = resumen_service.analyze_conversation(
            thread_id=request.threadId,
            messages=request.messages
        )
        
        return resultado
    
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error interno al procesar la solicitud: {str(e)}"
        )


@router.get("/resumen/health")
async def health_check() -> Dict[str, str]:
    """
    Health check específico del servicio de resumen.
    
    Returns:
        Estado del servicio
    """
    return {
        "status": "healthy",
        "service": "resumen_conversacional",
        "version": "1.0.0"
    }
