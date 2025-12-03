from typing import List
from pydantic import BaseModel


class SentimentInputItem(BaseModel):
    id: str
    text: str


class SentimentRequest(BaseModel):
    items: List[SentimentInputItem]


class SentimentResult(BaseModel):
    id: str
    sentiment: str  # "positivo" | "negativo" | "neutral"
    score: float
    explanation: str


class SentimentResponse(BaseModel):
    results: List[SentimentResult]
