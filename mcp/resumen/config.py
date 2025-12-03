"""
Configuración centralizada para el MCP de resumen conversacional.
Permite configuración vía variables de entorno con valores por defecto.
"""
import os
from pathlib import Path
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv()


class GeminiConfig:
    """Configuración para el cliente Gemini."""
    
    MODEL_NAME: str = os.getenv('GEMINI_MODEL_NAME', 'gemini-2.0-flash')
    
    TEMPERATURE: float = float(os.getenv('GEMINI_TEMPERATURE', '0.3'))
    TOP_P: float = float(os.getenv('GEMINI_TOP_P', '0.95'))
    TOP_K: int = int(os.getenv('GEMINI_TOP_K', '40'))
    MAX_OUTPUT_TOKENS: int = int(os.getenv('GEMINI_MAX_OUTPUT_TOKENS', '2048'))
    
    MAX_RETRIES: int = int(os.getenv('GEMINI_MAX_RETRIES', '3'))
    RETRY_BACKOFF_BASE: float = float(os.getenv('GEMINI_RETRY_BACKOFF', '1.5'))
    RETRY_QUOTA_BACKOFF: float = float(os.getenv('GEMINI_QUOTA_BACKOFF', '2.0'))
    
    SAFETY_BLOCK_NONE: bool = os.getenv('GEMINI_SAFETY_BLOCK_NONE', 'true').lower() == 'true'
    
    @classmethod
    def get_generation_config(cls) -> Dict[str, Any]:
        """Retorna configuración de generación para Gemini."""
        return {
            "temperature": cls.TEMPERATURE,
            "top_p": cls.TOP_P,
            "top_k": cls.TOP_K,
            "max_output_tokens": cls.MAX_OUTPUT_TOKENS,
        }
    
    @classmethod
    def get_safety_settings(cls):
        """Retorna configuración de seguridad para Gemini."""
        from google.generativeai.types import HarmCategory, HarmBlockThreshold
        
        if cls.SAFETY_BLOCK_NONE:
            return {
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            }
        return {}


class TextProcessingConfig:
    """Configuración para procesamiento de texto."""
    
    MAX_CONVERSATION_LENGTH: int = int(os.getenv('MAX_CONVERSATION_LENGTH', '100000'))
    TRUNCATE_MESSAGE: str = os.getenv(
        'TRUNCATE_MESSAGE', 
        '\n\n[... conversación truncada por longitud ...]'
    )
    
    CLEAN_HTML_ENTITIES: bool = os.getenv('CLEAN_HTML_ENTITIES', 'true').lower() == 'true'
    CLEAN_URLS: bool = os.getenv('CLEAN_URLS', 'true').lower() == 'true'
    NORMALIZE_WHITESPACE: bool = os.getenv('NORMALIZE_WHITESPACE', 'true').lower() == 'true'


class ServiceConfig:
    """Configuración general del servicio."""
    
    DEFAULT_PARQUET_PATH: Path = Path(__file__).parent.parent.parent / 'data' / 'clean' / 'Reto_data_20251023_122206.parquet'
    PARQUET_PATH: str = os.getenv('PARQUET_PATH', str(DEFAULT_PARQUET_PATH))
    
    GEMINI_API_KEY: str = os.getenv('GEMINI_API_KEY', '')
    
    SERVICE_VERSION: str = os.getenv('SERVICE_VERSION', '1.0.0')
    SERVICE_NAME: str = os.getenv('SERVICE_NAME', 'MCP Resumen Conversacional')
    
    @classmethod
    def validate(cls) -> None:
        """Valida que la configuración esté completa."""
        if not cls.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY no configurada en variables de entorno")
        
        if not Path(cls.PARQUET_PATH).exists():
            raise FileNotFoundError(f"Archivo Parquet no encontrado: {cls.PARQUET_PATH}")


config = ServiceConfig()

