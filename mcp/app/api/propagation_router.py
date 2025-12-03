from fastapi import APIRouter, HTTPException

from app.models.propagation_models import (
    PropagationRequest,
    PropagationResponse,
    PropagationSummary,
    LevelInfo,
    TimeBucket,
    TopReply,
)
from app.services.propagation_service import compute_propagation

router = APIRouter(prefix="/api/v1/analysis", tags=["propagation"])


@router.post("/propagation", response_model=PropagationResponse)
def analyze_propagation(payload: PropagationRequest) -> PropagationResponse:
    try:
        raw = compute_propagation(
            root_id=payload.root_id,
            messages=payload.messages,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    summary = PropagationSummary(**raw["summary"])
    levels = [LevelInfo(**lvl) for lvl in raw["levels"]]
    time_series = [TimeBucket(**tb) for tb in raw["time_series"]]
    top_replies = [TopReply(**t) for t in raw["top_engaged_replies"]]

    return PropagationResponse(
        root_id=raw["root_id"],
        summary=summary,
        levels=levels,
        time_series=time_series,
        top_engaged_replies=top_replies,
    )
