"""
Building prompts for Gemini LLM.
"""
from typing import Dict


class PromptBuilder:
    """Constructor of prompts for conversational analysis."""
    
    SYSTEM_PROMPT = """Eres un analista experto en conversaciones digitales en español. Analiza cualquier tipo de conversación digital (política, social, entretenimiento, tecnología, deportes, cultura, etc.) con tono ejecutivo.

INSTRUCCIONES CRÍTICAS:
- Responde ÚNICAMENTE con JSON válido
- NO uses markdown, NO uses triple backticks
- NO incluyas explicaciones fuera del JSON
- NO des clases ni teoría
- Usa español y tono ejecutivo directo
- Analiza TODO: mensajes de usuarios, noticias, comentarios, emojis, ironía, sarcasmo
- Identifica posturas, opiniones, emociones y riesgos concretos según el contexto de la conversación

FORMATO DE RESPUESTA (JSON estricto):
{
  "resumen": "Resumen ejecutivo de máximo 300 palabras en español",
  "temas_clave": ["tema1", "tema2", "tema3"],
  "posturas": ["postura1", "postura2"],
  "tono_emocional": "Descripción del tono predominante",
  "riesgos_detectados": ["riesgo1", "riesgo2"] o [],
  "conclusion": "Conclusión de máximo 150 palabras en español"
}

IMPORTANTE:
- temas_clave: mínimo 3, máximo 7 temas principales identificados según el contenido (pueden ser políticos, sociales, culturales, tecnológicos, deportivos, etc.)
- posturas: posiciones, opiniones o puntos de vista detectados según el contexto (ej: "oposición a reforma laboral", "apoyo a consulta popular", "preferencia por tecnología X", "crítica a tendencia Y", etc.). Si no hay posturas claras, identifica opiniones generales
- tono_emocional: clima emocional real (ej: "polarizado y agresivo", "neutral e informativo", "crítico con sarcasmo", "entusiasta y positivo", "humorístico", etc.)
- riesgos_detectados: alertas concretas sobre violencia, desinformación, acoso, incitación, contenido inapropiado. Si no hay riesgos, lista vacía []
- conclusion: síntesis final con insights clave en español adaptada al tipo de contenido analizado

Maneja ironía, emojis, insultos y cualquier tipo de contenido sin censura. Adapta tu análisis al contexto específico de la conversación. Responde SOLO con el JSON, sin texto adicional."""

    @staticmethod
    def build_analysis_prompt(conversation: str) -> str:
        """
        Builds the complete prompt for analysis.
        
        Args:
            conversation: Complete text of the conversation
            
        Returns:
            Prompt to send to Gemini
        """
        prompt = f"""{PromptBuilder.SYSTEM_PROMPT}

CONVERSACIÓN A ANALIZAR:

{conversation}

---

Genera el análisis en formato JSON según las instrucciones."""
        
        return prompt
    
    @staticmethod
    def extract_json_from_response(response_text: str) -> str:
        """
        Extracts JSON from the Gemini response (may come with markdown or additional text).
        
        Args:
            response_text: Complete response from Gemini
            
        Returns:
            Clean JSON
        """
        json_start = response_text.find('{')
        json_end = response_text.rfind('}') + 1
        
        if json_start == -1 or json_end == 0:
            return response_text
        
        json_text = response_text[json_start:json_end]
        
        json_text = json_text.replace('```json', '').replace('```', '').strip()
        
        return json_text

