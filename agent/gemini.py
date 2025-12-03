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
            history_context = "\n".join(
                [
                    f"Usuario: {msg.get('user', '')}\nAgente: {msg.get('agent', '')}"
                    for msg in conversation_history[-5:]
                ]
            )

        thread_id_context = ""
        if available_thread_id:
            thread_id_context = (
                f"\nTHREAD_ID DISPONIBLE EN CONTEXTO: {available_thread_id}\n"
                "(Usa este threadId si el usuario no especifica uno diferente)"
            )

        prompt = f"""
Eres un orquestador de herramientas MCP para análisis conversacional en español.
Debes decidir QUÉ herramienta usar y con QUÉ argumentos.

HERRAMIENTAS DISPONIBLES:
- mcp_resumen     -> Análisis completo de conversación (resumen ejecutivo, temas clave, posturas, tono, riesgos).
- mcp_sentiment   -> Análisis de emoción, sentimiento y clima emocional de uno o varios mensajes.
- mcp_propagation -> Análisis de propagación, engagement y viralidad a partir de un mensaje raíz.

CONTEXTO DE CONVERSACIÓN:
{history_context if history_context else "Nueva conversación"}
{thread_id_context}

PREGUNTA DEL USUARIO:
{user_query}

REGLAS DE DECISIÓN (MUY IMPORTANTES):
1) Usa mcp_sentiment cuando el foco principal sea:
   - emociones, sentimientos, clima, tono, polarización emocional
   - ejemplos: "¿qué sentimiento predomina?", "¿es positivo o negativo?", "¿cuál es el clima de esta conversación?"

2) Usa mcp_propagation cuando el foco principal sea:
   - propagación, viralidad, difusión, niveles de respuesta, cascadas, engagement
   - ejemplos: "¿qué tan viral fue este mensaje?", "analiza la propagación de este root", "qué tanta difusión tuvo"

3) Usa mcp_resumen cuando el usuario quiera:
   - un resumen ejecutivo completo
   - entender de qué trata la conversación, temas clave, posturas, narrativa y riesgos

4) Si la pregunta es general, chit-chat o no requiere análisis profundo,
   entonces tool = null y debes responder tú mismo en 'response'.

ARGUMENTOS ESPERADOS POR HERRAMIENTA:

- mcp_resumen:
  arguments = {{
    "threadId": "<ID del thread a analizar>"
  }}
  - Si el usuario menciona explícitamente un threadId, úsalo.
  - Si NO lo menciona, pero hay THREAD_ID DISPONIBLE EN CONTEXTO, úsalo.

- mcp_sentiment:
  arguments puede tener UNA de estas formas (elige la más adecuada):
  a) Análisis a nivel de thread completo (cuando el usuario solo da threadId):
     {{
       "threadId": "<threadId>"
     }}
  b) Análisis de mensajes específicos dentro de un thread:
     {{
       "threadId": "<threadId>",
       "messageIds": ["<id1>", "<id2>", ...]
     }}
  c) Análisis directo de items proporcionados en la conversación del usuario:
     {{
       "items": [
         {{"id": "1", "text": "texto del mensaje 1"}},
         {{"id": "2", "text": "texto del mensaje 2"}}
       ]
     }}

- mcp_propagation:
  arguments DEBE incluir siempre:
  {{
    "root_id": "<id del mensaje raíz>"
  }}
  Opcionalmente puede incluir:
  {{
    "messages": [{{ ... payload de mensajes ... }}]
  }}

FORMATO DE RESPUESTA (JSON ESTRICTO, SIN TEXTO ADICIONAL):
{{
  "tool": "mcp_resumen" | "mcp_sentiment" | "mcp_propagation" | null,
  "arguments": {{ ... }} | null,
  "response": null | "<respuesta directa en español si tool es null>"
}}

REGLAS ADICIONALES CRÍTICAS:
- Si eliges una herramienta (tool != null), 'response' DEBE ser null.
- Si tool es null, 'arguments' DEBE ser null y 'response' DEBE contener tu respuesta final.
- Si usas mcp_resumen y no tienes un threadId del usuario, usa el THREAD_ID DISPONIBLE EN CONTEXTO si existe.
- Nunca inventes IDs arbitrarios; si no puedes inferir un ID requerido, responde con tool = null y una explicación en 'response'.
- Responde SOLO con el JSON, sin comentarios, sin markdown, sin texto extra.
"""

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

