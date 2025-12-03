"""Main executable for the conversational agent."""
import os
import sys
from dotenv import load_dotenv
from .config import AgentConfig
from .gemini import GeminiClient
from .graph import create_agent_graph
from .memory import AgentState


def main():
    """Main entry point for the agent."""
    # Load environment variables
    load_dotenv()
    
    # Validate configuration
    try:
        AgentConfig.validate()
    except ValueError as e:
        print(f"Error de configuración: {e}")
        print("Asegúrate de tener GEMINI_API_KEY en tu archivo .env")
        sys.exit(1)
    
    # Initialize Gemini client
    try:
        gemini_client = GeminiClient()
    except Exception as e:
        print(f"Error inicializando Gemini: {e}")
        sys.exit(1)
    
    # Create agent graph
    graph = create_agent_graph(gemini_client)
    
    print("=" * 60)
    print("AGENTE CONVERSACIONAL - Análisis de Conversaciones")
    print("=" * 60)
    print("\nEscribe 'salir' o 'exit' para terminar.\n")
    
    # Initialize persistent state for conversation
    persistent_state = AgentState(user_query="")
    
    # Conversation loop
    while True:
        try:
            # Get user input
            user_query = input("\nUsuario: ").strip()
            
            if not user_query:
                continue
            
            if user_query.lower() in ["salir", "exit", "quit"]:
                print("\n¡Hasta luego!")
                break
            
            # Create state with previous context
            current_state = AgentState(user_query=user_query)
            # Preserve conversation history (deep copy)
            for msg in persistent_state.conversation_history:
                current_state.conversation_history.append(msg)
            # Preserve last analysis and thread ID
            current_state.last_analysis = persistent_state.last_analysis
            current_state.current_thread_id = persistent_state.current_thread_id
            
            # Convert to GraphState for LangGraph
            from .graph import state_to_dict, dict_to_state
            graph_state = state_to_dict(current_state)
            
            # Run graph
            print("\nProcesando...")
            final_graph_state = graph.invoke(graph_state)
            
            # Convert back to AgentState
            final_state = dict_to_state(final_graph_state)
            
            # Update persistent state with new information
            persistent_state = final_state
            
            # Display response
            print(f"\nAgente: {final_state.final_response}")
            
        except KeyboardInterrupt:
            print("\n\n¡Hasta luego!")
            break
        except Exception as e:
            print(f"\nError: {str(e)}")
            print("Por favor, intenta de nuevo.")


if __name__ == "__main__":
    main()

