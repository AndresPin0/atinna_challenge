from fastapi import FastAPI

from app.api.sentiment_router import router as sentiment_router
from app.api.propagation_router import router as propagation_router
from app.api.resumen_router import router as resumen_router

def create_app() -> FastAPI:
    app = FastAPI(
        title="MCP - Análisis Conversacional",
        description="Microservicios para análisis de sentimiento, propagación y resumen de conversaciones",
        version="1.0.0",
    )

    app.include_router(sentiment_router)
    app.include_router(propagation_router)
    app.include_router(resumen_router)
    return app


app = create_app()
