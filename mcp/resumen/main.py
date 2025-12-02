"""
FastAPI application para el MCP de resumen conversacional.
"""
import os
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

from .service import ResumenService
from .schemas import ResumenRequest, ResumenResponse, ErrorResponse

load_dotenv()

app = FastAPI(
    title="MCP Resumen Conversacional",
    description="Microservicio para generar resúmenes ejecutivos de conversaciones digitales",
    version="1.0.0"
)

PARQUET_PATH = os.getenv(
    'PARQUET_PATH',
    str(Path(__file__).parent.parent.parent / 'data' / 'clean' / 'Reto_data_20251023_122206.parquet')
)

try:
    resumen_service = ResumenService(PARQUET_PATH)
except Exception as e:
    resumen_service = None
    print(f"Advertencia: No se pudo inicializar el servicio: {e}")


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "service": "MCP Resumen Conversacional",
        "status": "running",
        "version": "1.0.0"
    }


@app.get("/health")
async def health():
    """Health check detallado."""
    if resumen_service is None:
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "error": "Servicio no inicializado"}
        )
    
    return {"status": "healthy", "parquet_path": PARQUET_PATH}


@app.post("/analisis/resumen", response_model=ResumenResponse)
async def generar_resumen(request: ResumenRequest):
    """
    Genera un resumen ejecutivo de una conversación por threadId.
    
    Args:
        request: Request con threadId
        
    Returns:
        ResumenResponse con el análisis estructurado
    """
    if resumen_service is None:
        raise HTTPException(
            status_code=503,
            detail="Servicio no inicializado. Verifica la configuración."
        )
    
    try:
        thread_info = resumen_service.get_thread_info(request.threadId)
        
        if thread_info['message_count'] == 0:
            raise HTTPException(
                status_code=404,
                detail=f"Thread {request.threadId} no encontrado o sin mensajes"
            )
        
        resultado = resumen_service.analyze_thread(request.threadId)
        
        return resultado
    
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error interno al procesar la solicitud: {str(e)}"
        )


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Manejador global de excepciones."""
    return JSONResponse(
        status_code=500,
        content={"error": "Error interno del servidor", "detail": str(exc)}
    )

