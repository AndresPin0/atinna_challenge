"""Gemini client for decision making and explanation."""
import json
from typing import Dict, Optional, Any
import google.generativeai as genai
from .config import AgentConfig


class GeminiClient:
    """Client for interacting with Google Gemini API."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Gemini client.
        
        Args:
            api_key: Gemini API key. If None, uses AgentConfig.get_gemini_api_key()
        """
        self.api_key = api_key or AgentConfig.get_gemini_api_key()
        if not self.api_key:
            raise ValueError("Gemini API key is required")
        
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(AgentConfig.get_gemini_model())
    
    def decide_tool(
        self, 
        user_query: str, 
        conversation_history: Optional[list] = None,
        available_thread_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Decides which tool to use based on user query.
        
        Args:
            user_query: The user's question
            conversation_history: Optional conversation history
            
        Returns:
            Dict with 'tool', 'arguments', and 'response' keys
        """
        history_context = ""
        if conversation_history:
            history_context = "\n".join([
                f"Usuario: {msg.get('user', '')}\nAgente: {msg.get('agent', '')}"
                for msg in conversation_history[-5:]
            ])
        
        thread_id_context = ""
        if available_thread_id:
            thread_id_context = f"\nTHREAD_ID DISPONIBLE EN CONTEXTO: {available_thread_id}\n(Usa este threadId si el usuario no especifica uno diferente)"
        
        prompt = f"""Eres un agente inteligente que decide cuándo usar herramientas de análisis.

CONTEXTO DE CONVERSACIÓN:
{history_context if history_context else "Nueva conversación"}
{thread_id_context}

PREGUNTA DEL USUARIO: {user_query}

INSTRUCCIONES:
- Analiza la intención del usuario
- Si la pregunta requiere análisis de conversación (resumen, clima emocional, temas, narrativa, posturas, riesgos), usa la herramienta mcp_resumen
- Si la pregunta es general o no requiere análisis, responde directamente (tool = null)

PALABRAS CLAVE que indican uso de herramienta:
- resumen, resumir, resumen ejecutivo
- clima, ambiente, tono emocional, sentimiento
- temas, temas clave, de qué hablan
- narrativa, historia, discusión
- posturas, opiniones, posiciones
- riesgos, problemas, alertas
- análisis, analizar

RESPUESTA REQUERIDA (JSON válido):
{{
  "tool": "mcp_resumen" | null,
  "arguments": {{ "threadId": "..." }} | null,
  "response": "..." | null
}}

IMPORTANTE:
- Si usas mcp_resumen, DEBES incluir threadId en arguments
- Si hay un THREAD_ID DISPONIBLE EN CONTEXTO, úsalo a menos que el usuario especifique uno diferente
- Si el usuario menciona un threadId específico en su pregunta, úsalo
- Si no hay threadId disponible y la pregunta requiere análisis, intenta extraerlo de la conversación o usa el disponible
- Si tool es null, DEBES incluir response con una respuesta directa
- Responde SOLO con el JSON, sin texto adicional"""

        try:
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            response_text = response_text.strip()
            
            decision = json.loads(response_text)
            
            if "tool" not in decision:
                raise ValueError("Missing 'tool' in decision response")
            
            return decision
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse Gemini decision response: {str(e)}. Response: {response_text[:200]}")
        except Exception as e:
            raise ValueError(f"Error calling Gemini for decision: {str(e)}")
    
    def explain_results(
        self, 
        mcp_response: Dict[str, Any], 
        original_query: str
    ) -> str:
        """
        Converts MCP JSON response into natural language explanation.
        
        Args:
            mcp_response: The JSON response from MCP
            original_query: The original user query
            
        Returns:
            Natural language explanation
        """
        prompt = f"""Eres un asistente que explica resultados de análisis de conversaciones de forma clara y natural.

PREGUNTA ORIGINAL DEL USUARIO: {original_query}

RESULTADOS DEL ANÁLISIS (JSON):
{json.dumps(mcp_response, indent=2, ensure_ascii=False)}

INSTRUCCIONES:
- Convierte estos resultados técnicos en una respuesta clara y humana
- Resalta los temas clave de forma destacada
- Menciona el tono emocional de manera natural
- Explica los riesgos detectados si los hay
- Usa un lenguaje profesional pero accesible
- Responde directamente a la pregunta del usuario
- No uses formato JSON ni listas técnicas
- Escribe en párrafos fluidos

RESPUESTA:"""

        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
            
        except Exception as e:
            raise ValueError(f"Error calling Gemini for explanation: {str(e)}")

