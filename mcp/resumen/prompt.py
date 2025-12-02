"""
Construcción de prompts para Gemini LLM.
"""
from typing import Dict


class PromptBuilder:
    """Constructor de prompts para análisis conversacional."""
    
    SYSTEM_PROMPT = """Eres un analista experto en conversaciones digitales en español. Analiza conversaciones políticas, sociales y de actualidad con tono ejecutivo.

INSTRUCCIONES CRÍTICAS:
- Responde ÚNICAMENTE con JSON válido
- NO uses markdown, NO uses triple backticks
- NO incluyas explicaciones fuera del JSON
- NO des clases ni teoría
- Usa español y tono ejecutivo directo
- Analiza TODO: mensajes de usuarios, noticias, comentarios, emojis, ironía, sarcasmo
- Identifica posturas políticas reales, emociones y riesgos concretos

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
- temas_clave: mínimo 3, máximo 7 temas principales identificados
- posturas: posiciones políticas, ideológicas o de opinión detectadas (ej: "oposición a reforma laboral", "apoyo a consulta popular")
- tono_emocional: clima emocional real (ej: "polarizado y agresivo", "neutral e informativo", "crítico con sarcasmo")
- riesgos_detectados: alertas concretas sobre violencia, desinformación, acoso, incitación. Si no hay riesgos, lista vacía []
- conclusion: síntesis final con insights clave en español

Maneja ironía, emojis, insultos y contenido político sin censura. Responde SOLO con el JSON, sin texto adicional."""

    @staticmethod
    def build_analysis_prompt(conversation: str) -> str:
        """
        Construye el prompt completo para análisis.
        
        Args:
            conversation: Texto completo de la conversación
            
        Returns:
            Prompt completo para enviar a Gemini
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
        Extrae JSON de la respuesta de Gemini (puede venir con markdown o texto adicional).
        
        Args:
            response_text: Respuesta completa de Gemini
            
        Returns:
            JSON limpio
        """
        json_start = response_text.find('{')
        json_end = response_text.rfind('}') + 1
        
        if json_start == -1 or json_end == 0:
            return response_text
        
        json_text = response_text[json_start:json_end]
        
        json_text = json_text.replace('```json', '').replace('```', '').strip()
        
        return json_text

