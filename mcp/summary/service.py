"""
Main service for the conversational analysis pipeline.
"""
import json
from typing import Dict, Optional
from .loader import ParquetLoader
from .cleaning import TextCleaner
from .prompt import PromptBuilder
from .gemini import GeminiClient
from .schemas import ResumenResponse
from .config import TextProcessingConfig


class ResumenService:
    """Service that executes the complete analysis pipeline."""
    
    def __init__(self, parquet_path: str, gemini_api_key: Optional[str] = None):
        """
        Initializes the service.
        
        Args:
            parquet_path: Path to the Parquet file
        """
        self.loader = ParquetLoader(parquet_path)
        self.cleaner = TextCleaner()
        self.prompt_builder = PromptBuilder()
        self.gemini_client = GeminiClient(api_key=gemini_api_key)
    
    def analyze_thread(self, thread_id: str) -> ResumenResponse:
        """
        Executes the complete analysis pipeline.
        
        Args:
            thread_id: ID of the thread to analyze
            
        Returns:
            ResumenResponse with the structured analysis
            
        Raises:
            ValueError: If the thread does not exist or there is an error in the analysis
        """
        conversation_raw = self.loader.get_conversation_text(thread_id)
        
        if not conversation_raw:
            raise ValueError(f"Thread {thread_id} not found or without messages")
        
        conversation_clean = self.cleaner.clean_conversation(conversation_raw)
        conversation_clean = self.cleaner.truncate_if_needed(
            conversation_clean, 
            max_length=TextProcessingConfig.MAX_CONVERSATION_LENGTH
        )
        
        prompt = self.prompt_builder.build_analysis_prompt(conversation_clean)
        
        try:
            response_text = self.gemini_client.generate_content(prompt)
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
            raise ValueError(f"Error parsing Gemini response: {str(e)}. Received response: {response_text[:500]}")
        except ValueError as e:
            raise
        except Exception as e:
            raise ValueError(f"Unexpected error generating analysis: {str(e)}")
    
    def get_thread_info(self, thread_id: str) -> Dict:
        """
        Gets basic information about the thread.
        
        Args:
            thread_id: ID of the thread
            
        Returns:
            Dictionary with metadata
        """
        return self.loader.get_thread_metadata(thread_id)

