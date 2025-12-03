from fastapi import APIRouter

from ..models.sentiment_models import (
    SentimentRequest,
    SentimentResponse,
    SentimentResult,
)
from ..services.sentiment_service import analyze_sentiment_batch

router = APIRouter(prefix="/api/v1/analysis", tags=["sentiment"])


@router.post("/sentiment", response_model=SentimentResponse)
def analyze_sentiment(payload: SentimentRequest) -> SentimentResponse:
    items = [{"id": item.id, "text": item.text} for item in payload.items]

    raw_results = analyze_sentiment_batch(items)

    parsed_results = [
        SentimentResult(
            id=r.get("id", ""),
            sentiment=r.get("sentiment", "neutral"),
            score=float(r.get("score", 0.0)),
            explanation=r.get("explanation", ""),
        )
        for r in raw_results
    ]

    return SentimentResponse(results=parsed_results)
