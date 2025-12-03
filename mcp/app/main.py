from fastapi import FastAPI

from app.api.sentiment_router import router as sentiment_router
from app.api.propagation_router import router as propagation_router

def create_app() -> FastAPI:
    app = FastAPI(
        title="MCP - Análisis de Sentimiento",
        version="1.0.0",
    )

    app.include_router(sentiment_router)
    app.include_router(propagation_router)
    return app


app = create_app()
