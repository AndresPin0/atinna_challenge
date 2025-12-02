"""
Construcción de prompts para Gemini LLM.
"""
from typing import Dict


class PromptBuilder:
    """Constructor de prompts para análisis conversacional."""
    
    SYSTEM_PROMPT = """Eres un analista experto en conversaciones digitales. Tu tarea es analizar conversaciones y generar un resumen ejecutivo estructurado.

INSTRUCCIONES CRÍTICAS:
- Responde ÚNICAMENTE con JSON válido
- NO uses markdown
- NO incluyas explicaciones fuera del JSON
- NO des clases ni teoría
- Usa tono ejecutivo y directo
- Analiza TODO el contenido: mensajes de usuarios, noticias, comentarios
- Identifica posturas, emociones y riesgos reales

FORMATO DE RESPUESTA (JSON estricto):
{
  "resumen": "Resumen ejecutivo de máximo 300 palabras",
  "temas_clave": ["tema1", "tema2", "tema3"],
  "posturas": ["postura1", "postura2"],
  "tono_emocional": "Descripción del tono predominante",
  "riesgos_detectados": ["riesgo1", "riesgo2"] o [],
  "conclusion": "Conclusión de máximo 150 palabras"
}

IMPORTANTE:
- temas_clave: mínimo 3, máximo 7 temas principales
- posturas: identifica posiciones políticas, ideológicas o de opinión
- tono_emocional: describe el clima emocional (ej: "polarizado y agresivo", "neutral e informativo")
- riesgos_detectados: alertas sobre violencia, desinformación, acoso, etc. Si no hay riesgos, lista vacía
- conclusion: síntesis final con insights clave

Responde SOLO con el JSON, sin texto adicional."""

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

