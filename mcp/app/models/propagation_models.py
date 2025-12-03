from typing import List, Optional
from pydantic import BaseModel


class PropagationMessage(BaseModel):
    id: str
    parentId: Optional[str] = None
    threadId: Optional[str] = None
    authorId: Optional[str] = None
    createdAt: str  # ISO 8601
    text: Optional[str] = None
    isComment: Optional[bool] = None
    isRetweet: Optional[bool] = None
    engagementRate: Optional[float] = 0.0
    influenceScore: Optional[float] = 0.0


class PropagationRequest(BaseModel):
    root_id: str
    messages: List[PropagationMessage]


class LevelInfo(BaseModel):
    depth: int
    count: int


class TimeBucket(BaseModel):
    bucket_start: str
    count: int


class TopReply(BaseModel):
    id: str
    authorId: Optional[str]
    createdAt: str
    engagementRate: float
    influenceScore: float
    depth: int
    content_overlap: float


class PropagationSummary(BaseModel):
    total_replies: int
    direct_replies: int
    indirect_replies: int
    unique_authors: int
    max_depth: int
    time_to_first_reply_minutes: float
    time_to_50pct_replies_minutes: float
    avg_content_overlap: float
    propagation_score: float


class PropagationResponse(BaseModel):
    root_id: str
    summary: PropagationSummary
    levels: List[LevelInfo]
    time_series: List[TimeBucket]
    top_engaged_replies: List[TopReply]
