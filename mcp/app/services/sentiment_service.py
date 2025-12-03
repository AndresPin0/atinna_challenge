from typing import List, Dict, Any

from ..core.config import settings
from ..llm.gemini_client import GeminiSentimentClient


client = GeminiSentimentClient()


def analyze_sentiment_batch(items: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    """
    Capa de dominio:
    - Divide en batches
    - Llama al cliente Gemini
    - Fusiona resultados
    """
    batch_size = settings.BATCH_SIZE
    results: List[Dict[str, Any]] = []

    for i in range(0, len(items), batch_size):
        chunk = items[i:i + batch_size]
        chunk_results = client.analyze(chunk)
        results.extend(chunk_results)

    return results
