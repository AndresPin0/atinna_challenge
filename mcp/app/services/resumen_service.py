"""
Servicio principal para generación de resúmenes conversacionales.
"""
import json
from typing import List
from ..models.resumen_models import MessageInput, ResumenResponse
from ..services.text_cleaning_service import TextCleaningService
from ..services.prompt_builder import PromptBuilder
from ..llm.gemini_client import GeminiClient


class ResumenService:
    """Servicio que ejecuta el pipeline completo de análisis conversacional."""
    
    def __init__(self):
        """Inicializa el servicio con cliente Gemini unificado."""
        self.gemini_client = GeminiClient()
        self.text_cleaner = TextCleaningService()
        self.prompt_builder = PromptBuilder()
    
    def analyze_conversation(
        self, 
        thread_id: str, 
        messages: List[MessageInput]
    ) -> ResumenResponse:
        """
        Ejecuta el pipeline completo de análisis conversacional.
        
        Args:
            thread_id: ID del thread de conversación
            messages: Lista de mensajes a analizar
            
        Returns:
            ResumenResponse con el análisis estructurado
            
        Raises:
            ValueError: Si hay error en el análisis o mensajes vacíos
        """
        # Validar que hay mensajes
        if not messages:
            raise ValueError("No se proporcionaron mensajes para analizar")
        
        # Construir texto de conversación limpio
        conversation_text = self.text_cleaner.build_conversation_text(messages)
        
        if not conversation_text.strip():
            raise ValueError("Todos los mensajes están vacíos o sin texto válido")
        
        # Truncar si es necesario para evitar límites de API
        conversation_text = self.text_cleaner.truncate_if_needed(
            conversation_text, 
            max_length=100000
        )
        
        # Construir prompt para Gemini
        prompt = self.prompt_builder.build_analysis_prompt(conversation_text)
        
        # Generar análisis con Gemini
        try:
            response_text = self.gemini_client.generate_content(
                prompt=prompt,
                temperature=0.1,
                max_output_tokens=8192
            )
            
            if not response_text:
                raise ValueError("Respuesta vacía de Gemini")
            
            # Extraer y limpiar JSON de la respuesta
            json_text = self.prompt_builder.extract_json_from_response(response_text)
            
            # Parsear JSON
            analysis_data = json.loads(json_text)
            
            # Validar y completar campos faltantes
            validated_data = self.prompt_builder.validate_analysis_response(analysis_data)
            
            # Construir respuesta
            return ResumenResponse(
                threadId=thread_id,
                resumen=validated_data['resumen'],
                temas_clave=validated_data['temas_clave'],
                posturas=validated_data['posturas'],
                tono_emocional=validated_data['tono_emocional'],
                riesgos_detectados=validated_data['riesgos_detectados'],
                conclusion=validated_data['conclusion'],
                message_count=len(messages)
            )
        
        except json.JSONDecodeError as e:
            raise ValueError(
                f"Error al parsear respuesta JSON de Gemini: {str(e)}. "
                f"Respuesta recibida: {response_text[:500] if isinstance(response_text, str) else str(response_text)[:500]}"
            )
        except Exception as e:
            raise ValueError(f"Error al generar análisis: {str(e)}")
    
    async def analyze_conversation_async(
        self, 
        thread_id: str, 
        messages: List[MessageInput]
    ) -> ResumenResponse:
        """
        Versión asíncrona del análisis conversacional.
        
        Args:
            thread_id: ID del thread de conversación
            messages: Lista de mensajes a analizar
            
        Returns:
            ResumenResponse con el análisis estructurado
        """
        # Por ahora, delegar a la versión síncrona
        # En el futuro se puede implementar con aiohttp si Gemini lo soporta
        return self.analyze_conversation(thread_id, messages)

