import json
import re
from typing import List, Dict, Any, Optional

from google import genai

from app.core.config import settings


class GeminiClient:
    """Cliente unificado para interactuar con Google Gemini."""
    
    def __init__(self) -> None:
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self.model = settings.GEMINI_MODEL
    
    def generate_content(
        self, 
        prompt: str, 
        temperature: float = 0.1, 
        max_output_tokens: int = 8192
    ) -> str:
        """
        Genera contenido usando Gemini.
        
        Args:
            prompt: Prompt a enviar
            temperature: Temperatura para generación (0.0-1.0)
            max_output_tokens: Máximo de tokens en la respuesta
            
        Returns:
            Texto de respuesta de Gemini
            
        Raises:
            ValueError: Si no hay respuesta válida
        """
        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            config={
                "temperature": temperature,
                "max_output_tokens": max_output_tokens,
            },
        )

        # Extract text from response
        raw_text = self._extract_text_from_response(response)
        
        if raw_text is None:
            raise ValueError(f"No text content in response. Response: {response}")
        
        return raw_text
    
    def _extract_text_from_response(self, response) -> Optional[str]:
        """Extrae texto de diferentes formatos de respuesta de Gemini."""
        # Try direct text attribute
        if hasattr(response, 'text') and response.text:
            return response.text
        
        # Try to get text from candidates
        if hasattr(response, 'candidates') and response.candidates:
            candidate = response.candidates[0]
            if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                parts = candidate.content.parts
                if parts and hasattr(parts[0], 'text'):
                    return parts[0].text
        
        return None
    
    @staticmethod
    def clean_json_response(raw_text: str) -> str:
        """
        Limpia la respuesta removiendo markdown y espacios.
        
        Args:
            raw_text: Texto crudo de la respuesta
            
        Returns:
            Texto limpio
        """
        raw_text = raw_text.strip()
        
        # Remove markdown code blocks
        if raw_text.startswith("```json"):
            raw_text = raw_text[7:]
        if raw_text.startswith("```"):
            raw_text = raw_text[3:]
        if raw_text.endswith("```"):
            raw_text = raw_text[:-3]
        
        return raw_text.strip()
    
    @staticmethod
    def extract_json_from_text(text: str) -> str:
        """
        Extrae JSON de un texto que puede contener contenido adicional.
        
        Args:
            text: Texto que contiene JSON
            
        Returns:
            JSON extraído
            
        Raises:
            ValueError: Si no se encuentra JSON válido
        """
        # Find JSON delimiters
        json_start = text.find('{')
        json_end = text.rfind('}') + 1
        
        if json_start == -1 or json_end == 0:
            # Try to find array
            json_start = text.find('[')
            json_end = text.rfind(']') + 1
        
        if json_start == -1 or json_end == 0:
            raise ValueError(f"No JSON found in text: {text[:200]}")
        
        return text[json_start:json_end]
    
    @staticmethod
    def recover_partial_json_array(raw_text: str) -> List[Dict[str, Any]]:
        """
        Intenta recuperar objetos JSON válidos de una respuesta parcial/incompleta.
        
        Args:
            raw_text: Texto con JSON posiblemente incompleto
            
        Returns:
            Lista de objetos JSON válidos recuperados
        """
        valid_objects = []
        
        # Find all complete JSON objects
        matches = re.findall(r'\{[^}]+\}', raw_text)
        
        for match in matches:
            try:
                obj = json.loads(match)
                valid_objects.append(obj)
            except json.JSONDecodeError:
                continue
        
        return valid_objects


class GeminiSentimentClient:
    """Cliente especializado para análisis de sentimiento (mantiene compatibilidad)."""
    
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
    
    def __init__(self) -> None:
        self.gemini_client = GeminiClient()

    def analyze(self, items: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """
        Analiza el sentimiento de una lista de mensajes.
        
        Args:
            items: [{"id": str, "text": str}, ...]
            
        Returns:
            [{"id", "sentiment", "score", "explanation"}, ...]
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
        prompt = self.SENTIMENT_PROMPT.replace("{{items_json}}", items_json)

        try:
            raw_text = self.gemini_client.generate_content(prompt)
        except ValueError as e:
            print(f"Warning: {e}")
            return []

        # Clean the response
        raw_text = GeminiClient.clean_json_response(raw_text)

        try:
            parsed = json.loads(raw_text)
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}")
            print(f"Raw text: {raw_text[:500]}...")
            
            # Try to recover partial JSON
            valid_objects = GeminiClient.recover_partial_json_array(raw_text)
            if valid_objects:
                # Filter to only sentiment results
                sentiment_objects = [
                    obj for obj in valid_objects 
                    if 'id' in obj and 'sentiment' in obj
                ]
                if sentiment_objects:
                    print(f"Recovered {len(sentiment_objects)} valid objects from partial response")
                    return sentiment_objects
            
            return []

        if not isinstance(parsed, list):
            parsed = [parsed]

        return parsed

