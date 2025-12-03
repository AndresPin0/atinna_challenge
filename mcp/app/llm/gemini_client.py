import json
from typing import List, Dict, Any

from google import genai

from app.core.config import settings


SENTIMENT_PROMPT = """
Analiza el sentimiento de estos mensajes y responde SOLO con un array JSON válido.

Formato requerido:
{
  "id": "<id>",
  "sentiment": "positivo" | "negativo" | "neutral",
  "score": <0.0-1.0>,
  "explanation": "<máximo 10 palabras>"
}

Mensajes:
{{items_json}}

Responde ÚNICAMENTE el array JSON:
"""


class GeminiSentimentClient:
    def __init__(self) -> None:
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self.model = settings.GEMINI_MODEL

    def analyze(self, items: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """
        items: [{"id": str, "text": str}, ...]
        return: [{"id", "sentiment", "score", "explanation"}, ...]
        """
        # Truncate very long texts to avoid token limits
        truncated_items = []
        for item in items:
            truncated_item = item.copy()
            text = truncated_item.get('text', '')
            if len(text) > 500:
                truncated_item['text'] = text[:500] + '...'
            truncated_items.append(truncated_item)
        
        items_json = json.dumps(truncated_items, ensure_ascii=False)
        prompt = SENTIMENT_PROMPT.replace("{{items_json}}", items_json)

        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            config={
                "temperature": 0.1,
                "max_output_tokens": 8192,
            },
        )

        # Check if response has text
        raw_text = response.text if hasattr(response, 'text') and response.text else None
        
        if raw_text is None:
            # Try to get text from candidates if available
            if hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                    parts = candidate.content.parts
                    if parts and hasattr(parts[0], 'text'):
                        raw_text = parts[0].text
        
        if raw_text is None:
            print(f"Warning: No text content in response. Response: {response}")
            return []

        # Clean the response - remove markdown code blocks if present
        raw_text = raw_text.strip()
        if raw_text.startswith("```json"):
            raw_text = raw_text[7:]
        if raw_text.startswith("```"):
            raw_text = raw_text[3:]
        if raw_text.endswith("```"):
            raw_text = raw_text[:-3]
        raw_text = raw_text.strip()

        try:
            parsed = json.loads(raw_text)
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}")
            print(f"Raw text: {raw_text[:500]}...")  # Print first 500 chars only
            
            # Try to extract valid JSON objects from incomplete response
            try:
                # Find the last complete object by looking for the last complete entry
                # This handles cases where response was cut off mid-generation
                import re
                # Try to find array of complete objects
                matches = re.findall(r'\{[^}]+\}', raw_text)
                if matches:
                    valid_objects = []
                    for match in matches:
                        try:
                            obj = json.loads(match)
                            if 'id' in obj and 'sentiment' in obj:
                                valid_objects.append(obj)
                        except:
                            continue
                    if valid_objects:
                        print(f"Recovered {len(valid_objects)} valid objects from partial response")
                        return valid_objects
            except Exception as recovery_error:
                print(f"Recovery attempt failed: {recovery_error}")
            
            return []

        if not isinstance(parsed, list):
            parsed = [parsed]

        return parsed
