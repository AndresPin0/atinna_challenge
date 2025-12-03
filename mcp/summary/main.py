"""
FastAPI application for the Conversational Summary MCP.
"""
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

from .service import ResumenService
from .schemas import ResumenRequest, ResumenResponse, ErrorResponse
from .config import ServiceConfig, GeminiConfig

try:
    ServiceConfig.validate()
except (ValueError, FileNotFoundError) as e:
    print(f"Configuration error: {e}")

app = FastAPI(
    title=ServiceConfig.SERVICE_NAME,
    description="Microservice for generating executive summaries of digital conversations",
    version=ServiceConfig.SERVICE_VERSION
)

try:
    resumen_service = ResumenService(ServiceConfig.PARQUET_PATH)
except Exception as e:
    resumen_service = None
    print(f"Warning: Could not initialize the service: {e}")


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "service": ServiceConfig.SERVICE_NAME,
        "status": "running",
        "version": ServiceConfig.SERVICE_VERSION
    }


@app.get("/health")
async def health():
    """Detailed health check."""
    if resumen_service is None:
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "error": "Service not initialized"}
        )
    
    return {
        "status": "healthy", 
        "parquet_path": ServiceConfig.PARQUET_PATH,
        "model": GeminiConfig.MODEL_NAME
    }


@app.post("/analisis/resumen", response_model=ResumenResponse)
async def generate_summary(request: ResumenRequest):
    """
    Generates an executive summary of a conversation by threadId.
    
    Args:
        request: Request with threadId
        
    Returns:
        ResumenResponse with the structured analysis
    """
    if resumen_service is None:
        raise HTTPException(
            status_code=503,
            detail="Service not initialized. Verify the configuration."
        )
    
    try:
        thread_info = resumen_service.get_thread_info(request.threadId)
        
        if thread_info['message_count'] == 0:
            raise HTTPException(
                status_code=404,
                detail=f"Thread {request.threadId} not found or without messages"
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
            detail=f"Internal error processing the request: {str(e)}"
        )


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": str(exc)}
    )

