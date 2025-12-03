"""Node implementations for the LangGraph."""
from typing import Dict, Any, List, Optional
import httpx
from .memory import AgentState
from .router import Router
from .gemini import GeminiClient
from .config import AgentConfig
from .tools import MCPResumenResponse
from .parquet_Loader import AgentParquetLoader


class AgentNodes:
    """Collection of agent nodes for LangGraph."""

    MAX_SENTIMENT_ITEMS: int = 120
    
    def __init__(self, gemini_client: GeminiClient):
        """
        Initialize agent nodes.
        
        Args:
            gemini_client: Gemini client instance
        """
        self.gemini_client = gemini_client
        self.router = Router(gemini_client)
        try:
                parquet_path = AgentConfig.get_parquet_path()
                if parquet_path:
                    self.parquet_loader = AgentParquetLoader(parquet_path)
                else:
                    self.parquet_loader = None
        except Exception as e:
            print(f"Warning: No se pudo inicializar ParquetLoader: {e}")
            self.parquet_loader = None


    def decide_node(self, state: AgentState) -> Dict[str, Any]:
        """
        Decision node: determines which tool to use.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state with tool_decision
        """
        try:
            decision = self.router.decide(state)
            return {"tool_decision": decision}
        except Exception as e:
            # On error, default to no tool
            return {
                "tool_decision": {
                    "tool": None,
                    "arguments": None,
                    "response": f"Lo siento, hubo un error al procesar tu solicitud: {str(e)}"
                }
            }
    
    def resumen_node(self, state: AgentState) -> Dict[str, Any]:
        """
        Resumen node: calls MCP resumen endpoint.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state with mcp_response
        """
        if not state.tool_decision:
            raise ValueError("No tool decision available")
        
        if state.tool_decision["tool"] != "mcp_resumen":
            raise ValueError(f"Invalid tool for resumen_node: {state.tool_decision['tool']}")
        
        thread_id = state.tool_decision["arguments"]["threadId"]
        
        if not self.parquet_loader:
            raise ValueError("ParquetLoader no está configurado. Configura PARQUET_PATH en variables de entorno.")
        
        try:
            messages = self.parquet_loader.load_thread_messages(thread_id)
        except ValueError as e:
            raise ValueError(f"Error cargando mensajes desde Parquet: {str(e)}")
        
        payload = {
            "threadId": thread_id,
            "messages": messages
        }
        
        try:
            with httpx.Client(timeout=AgentConfig.REQUEST_TIMEOUT) as client:
                response = client.post(
                    AgentConfig.get_mcp_resumen_url(),
                    json=payload
                )
                response.raise_for_status()
                mcp_data = response.json()
                
                # Validate response structure
                mcp_response = MCPResumenResponse(**mcp_data)
                
                return {
                    "mcp_response": mcp_response.to_dict(),
                    "current_thread_id": thread_id
                }
                
        except httpx.HTTPStatusError as e:
            raise ValueError(f"MCP endpoint error: {e.response.status_code} - {e.response.text}")
        except httpx.RequestError as e:
            raise ValueError(f"Error calling MCP endpoint: {str(e)}")
        except Exception as e:
            raise ValueError(f"Unexpected error in resumen_node: {str(e)}")

    def sentiment_node(self, state: AgentState) -> Dict[str, Any]:
        """
        Sentiment node: calls MCP sentiment endpoint.

        Args:
            state: Current agent state

        Returns:
            Updated state with mcp_response and tool_used
        """
        if not state.tool_decision:
            raise ValueError("No tool decision available")

        if state.tool_decision["tool"] != "mcp_sentiment":
            raise ValueError(
                f"Invalid tool for sentiment_node: {state.tool_decision['tool']}"
            )

        arguments = dict(state.tool_decision.get("arguments") or {})

        try:
            payload = self._build_sentiment_payload(arguments, state)

            with httpx.Client(timeout=AgentConfig.REQUEST_TIMEOUT) as client:
                response = client.post(
                    AgentConfig.get_mcp_sentiment_url(),
                    json=payload,
                )
                response.raise_for_status()
                mcp_data = response.json()

                return {
                    "mcp_response": mcp_data,
                    "tool_used": "mcp_sentiment",
                }

        except httpx.HTTPStatusError as e:
            raise ValueError(f"MCP endpoint error: {e.response.status_code} - {e.response.text}")
        except httpx.RequestError as e:
            raise ValueError(f"Error calling MCP endpoint: {str(e)}")
        except Exception as e:
            raise ValueError(f"Unexpected error in sentiment_node: {str(e)}")

    def propagation_node(self, state: AgentState) -> Dict[str, Any]:
        """
        Propagation node: calls MCP propagation endpoint.

        Args:
            state: Current agent state

        Returns:
            Updated state with mcp_response and tool_used
        """
        if not state.tool_decision:
            raise ValueError("No tool decision available")

        if state.tool_decision["tool"] != "mcp_propagation":
            raise ValueError(
                f"Invalid tool for propagation_node: {state.tool_decision['tool']}"
            )

        arguments = dict(state.tool_decision.get("arguments") or {})

        try:
            # Si no se proporcionan mensajes, construirlos desde el Parquet
            if "messages" not in arguments or not arguments["messages"]:
                root_id = arguments.get("root_id")
                if not root_id:
                    raise ValueError("mcp_propagation requires 'root_id' in arguments")

                if not self.parquet_loader:
                    raise ValueError(
                        "ParquetLoader no está configurado. Configura PARQUET_PATH en variables de entorno."
                    )

                messages = self.parquet_loader.load_propagation_messages(root_id)
                arguments["messages"] = messages

            with httpx.Client(timeout=AgentConfig.REQUEST_TIMEOUT) as client:
                response = client.post(
                    AgentConfig.get_mcp_propagation_url(),
                    json=arguments,
                )
                response.raise_for_status()
                mcp_data = response.json()

                return {
                    "mcp_response": mcp_data,
                    "tool_used": "mcp_propagation",
                }

        except httpx.HTTPStatusError as e:
            raise ValueError(f"MCP endpoint error: {e.response.status_code} - {e.response.text}")
        except httpx.RequestError as e:
            raise ValueError(f"Error calling MCP endpoint: {str(e)}")
        except Exception as e:
            raise ValueError(f"Unexpected error in propagation_node: {str(e)}")

    def _build_sentiment_payload(
        self,
        arguments: Dict[str, Any],
        state: AgentState,
    ) -> Dict[str, Any]:
        """
        Ensure sentiment requests include the required 'items' payload.
        """
        payload = dict(arguments)

        # If caller already provided items, trust them.
        if payload.get("items"):
            payload["items"] = payload["items"][-self.MAX_SENTIMENT_ITEMS :]
            return payload

        thread_id = self._resolve_thread_id(payload.get("threadId"), state)

        if not self.parquet_loader:
            raise ValueError(
                "ParquetLoader no está configurado. Configura PARQUET_PATH en variables de entorno."
            )

        try:
            messages = self.parquet_loader.load_thread_messages(thread_id)
        except ValueError as e:
            raise ValueError(f"Error cargando mensajes desde Parquet: {str(e)}")

        message_ids = payload.get("messageIds")
        if message_ids:
            ids_set = set(message_ids)
            filtered = [msg for msg in messages if msg.get("id") in ids_set]
        else:
            filtered = messages

        # keep only most recent subset
        filtered = filtered[-self.MAX_SENTIMENT_ITEMS :]

        items: List[Dict[str, str]] = []
        for msg in filtered:
            text = (msg.get("text") or "").strip()
            if not text:
                continue
            msg_id = str(msg.get("id", ""))
            if not msg_id:
                continue
            items.append({"id": msg_id, "text": text})

        if not items:
            raise ValueError(
                "No hay mensajes con texto válido para análisis de sentimiento"
            )

        payload["threadId"] = thread_id
        payload["items"] = items
        return payload

    def _resolve_thread_id(
        self, requested_thread: Optional[str], state: AgentState
    ) -> str:
        """Resolve threadId from arguments or conversational context."""
        if requested_thread:
            return requested_thread
        if state.current_thread_id:
            return state.current_thread_id
        if state.last_analysis:
            return state.last_analysis.thread_id
        raise ValueError(
            "Sentiment analysis requires 'threadId' or explicit 'items' in arguments"
        )
    
    def explain_node(self, state: AgentState) -> Dict[str, Any]:
        """
        Explanation node: converts MCP JSON to natural language.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state with explanation
        """
        if not state.mcp_response:
            raise ValueError("No MCP response available")
        
        try:
            explanation = self.gemini_client.explain_results(
                mcp_response=state.mcp_response,
                original_query=state.user_query
            )
            
            return {"explanation": explanation}
            
        except Exception as e:
            # Fallback to structured explanation
            mcp = state.mcp_response
            explanation = f"""Resumen: {mcp.get('resumen', 'No disponible')}

Temas clave: {', '.join(mcp.get('temas_clave', [])) if mcp.get('temas_clave') else 'No identificados'}

Tono emocional: {mcp.get('tono_emocional', 'No determinado')}

Riesgos detectados: {', '.join(mcp.get('riesgos_detectados', [])) if mcp.get('riesgos_detectados') else 'Ninguno'}

Conclusión: {mcp.get('conclusion', 'No disponible')}"""
            
            return {"explanation": explanation}
    
    def memory_node(self, state: AgentState) -> Dict[str, Any]:
        """
        Memory node: saves analysis to memory.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state (no changes, but saves to memory)
        """
        if state.mcp_response and state.current_thread_id:
            state.save_analysis(
                thread_id=state.current_thread_id,
                resumen=state.mcp_response.get("resumen", ""),
                tono_emocional=state.mcp_response.get("tono_emocional", ""),
                temas_clave=state.mcp_response.get("temas_clave", [])
            )
        
        return {}
    
    def respond_node(self, state: AgentState) -> Dict[str, Any]:
        """
        Response node: generates final response to user.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state with final_response
        """
        # If we have an explanation from MCP, use it
        if state.explanation:
            final_response = state.explanation
        # If router provided direct response, use it
        elif state.tool_decision and state.tool_decision.get("response"):
            final_response = state.tool_decision["response"]
        # Fallback
        else:
            final_response = "Lo siento, no pude procesar tu solicitud correctamente."
        
        # Add message to conversation history
        state.add_message(user=state.user_query, agent=final_response)
        
        return {"final_response": final_response}

