"""
Servicio principal del pipeline de análisis conversacional.
"""
import json
import os
from typing import Dict, Optional
import google.generativeai as genai
from .loader import ParquetLoader
from .cleaning import TextCleaner
from .prompt import PromptBuilder
from .schemas import ResumenResponse


class ResumenService:
    """Servicio que ejecuta el pipeline completo de análisis."""
    
    def __init__(self, parquet_path: str, gemini_api_key: Optional[str] = None):
        """
        Inicializa el servicio.
        
        Args:
            parquet_path: Ruta al archivo Parquet
            gemini_api_key: API key de Gemini (o desde env)
        """
        self.loader = ParquetLoader(parquet_path)
        self.cleaner = TextCleaner()
        self.prompt_builder = PromptBuilder()
        
        api_key = gemini_api_key or os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY no configurada.")
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-pro')
    
    def analyze_thread(self, thread_id: str) -> ResumenResponse:
        """
        Ejecuta el pipeline completo de análisis.
        
        Args:
            thread_id: ID del thread a analizar
            
        Returns:
            ResumenResponse con el análisis estructurado
            
        Raises:
            ValueError: Si el thread no existe o hay error en el análisis
        """
        conversation_raw = self.loader.get_conversation_text(thread_id)
        
        if not conversation_raw:
            raise ValueError(f"Thread {thread_id} no encontrado o sin mensajes")
        
        conversation_clean = self.cleaner.clean_conversation(conversation_raw)
        
        conversation_clean = self.cleaner.truncate_if_needed(conversation_clean, max_length=100000)
        
        prompt = self.prompt_builder.build_analysis_prompt(conversation_clean)
        
        try:
            response = self.model.generate_content(prompt)
            response_text = response.text
            
            json_text = self.prompt_builder.extract_json_from_response(response_text)
            
            analysis_data = json.loads(json_text)
            
            return ResumenResponse(
                resumen=analysis_data.get('resumen', ''),
                temas_clave=analysis_data.get('temas_clave', []),
                posturas=analysis_data.get('posturas', []),
                tono_emocional=analysis_data.get('tono_emocional', ''),
                riesgos_detectados=analysis_data.get('riesgos_detectados', []),
                conclusion=analysis_data.get('conclusion', '')
            )
        
        except json.JSONDecodeError as e:
            raise ValueError(f"Error al parsear respuesta de Gemini: {str(e)}. Respuesta: {response_text[:500]}")
        except Exception as e:
            raise ValueError(f"Error al generar análisis: {str(e)}")
    
    def get_thread_info(self, thread_id: str) -> Dict:
        """
        Obtiene información básica del thread.
        
        Args:
            thread_id: ID del thread
            
        Returns:
            Diccionario con metadatos
        """
        return self.loader.get_thread_metadata(thread_id)

