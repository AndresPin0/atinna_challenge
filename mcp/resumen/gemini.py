"""
Cliente para la API de Google Gemini.
Maneja conexión, errores y retry logic.
"""
import os
import time
from typing import Optional
import google.generativeai as genai
from .config import GeminiConfig


class GeminiClient:
    """Cliente para interactuar con la API de Gemini."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Inicializa el cliente Gemini.
        
        Args:
            api_key: API key de Gemini. Si no se proporciona, se lee de GEMINI_API_KEY
        """
        from .config import ServiceConfig
        api_key = api_key or ServiceConfig.GEMINI_API_KEY
        if not api_key:
            raise ValueError("GEMINI_API_KEY no configurada en variables de entorno")
        
        genai.configure(api_key=api_key)
        
        safety_settings = GeminiConfig.get_safety_settings()
        generation_config = GeminiConfig.get_generation_config()
        
        self.model = genai.GenerativeModel(
            model_name=GeminiConfig.MODEL_NAME,
            safety_settings=safety_settings,
            generation_config=generation_config
        )
    
    def generate_content(self, prompt: str, max_retries: Optional[int] = None) -> str:
        """
        Genera contenido usando Gemini con manejo de errores y retry.
        
        Args:
            prompt: Prompt a enviar a Gemini
            max_retries: Número máximo de reintentos
            
        Returns:
            Texto de respuesta de Gemini
            
        Raises:
            ValueError: Si hay error en la API después de todos los reintentos
        """
        max_retries = max_retries or GeminiConfig.MAX_RETRIES
        last_error = None
        
        for attempt in range(max_retries):
            try:
                response = self.model.generate_content(prompt)
                
                if not response.text:
                    raise ValueError("Respuesta vacía de Gemini")
                
                return response.text
            
            except Exception as e:
                last_error = e
                error_str = str(e).lower()
                
                if "api key" in error_str or "authentication" in error_str:
                    raise ValueError(f"Error de autenticación con Gemini: {str(e)}")
                
                if "quota" in error_str or "rate limit" in error_str:
                    wait_time = (attempt + 1) * GeminiConfig.RETRY_QUOTA_BACKOFF
                    if attempt < max_retries - 1:
                        time.sleep(wait_time)
                        continue
                    raise ValueError(f"Límite de cuota excedido en Gemini: {str(e)}")
                
                if "safety" in error_str or "blocked" in error_str:
                    raise ValueError(f"Contenido bloqueado por políticas de seguridad: {str(e)}")
                
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * GeminiConfig.RETRY_BACKOFF_BASE
                    time.sleep(wait_time)
                    continue
                else:
                    raise ValueError(f"Error al generar contenido con Gemini (intentos agotados): {str(e)}")
        
        raise ValueError(f"Error al generar contenido: {str(last_error)}")
    
    def is_available(self) -> bool:
        """
        Verifica si el cliente está disponible y configurado correctamente.
        
        Returns:
            True si el cliente está disponible
        """
        try:
            test_response = self.model.generate_content("test")
            return test_response.text is not None
        except Exception:
            return False

