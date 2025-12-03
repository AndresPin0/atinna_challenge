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
    load_dotenv()
    
    try:
        AgentConfig.validate()
    except ValueError as e:
        print(f"Error de configuración: {e}")
        print("Asegúrate de tener GEMINI_API_KEY en tu archivo .env")
        sys.exit(1)
    
    try:
        gemini_client = GeminiClient()
    except Exception as e:
        print(f"Error inicializando Gemini: {e}")
        sys.exit(1)
    
    graph = create_agent_graph(gemini_client)
    
    print("AGENTE CONVERSACIONAL")
    print("\nEscribe 'salir' o 'exit' para terminar.\n")
    
    persistent_state = AgentState(user_query="")
    
    while True:
        try:
            user_query = input("\nUsuario: ").strip()
            
            if not user_query:
                continue
            
            if user_query.lower() in ["salir", "exit", "quit"]:
                print("\n¡Hasta luego!")
                break
            
            current_state = AgentState(user_query=user_query)
            for msg in persistent_state.conversation_history:
                current_state.conversation_history.append(msg)
            current_state.last_analysis = persistent_state.last_analysis
            current_state.current_thread_id = persistent_state.current_thread_id
            
            from .graph import state_to_dict, dict_to_state
            graph_state = state_to_dict(current_state)
            
            print("\nProcesando...")
            final_graph_state = graph.invoke(graph_state)
            
            final_state = dict_to_state(final_graph_state)
            
            persistent_state = final_state
            
            print(f"\nAgente: {final_state.final_response}")
            
        except KeyboardInterrupt:
            print("\n\n¡Hasta luego!")
            break
        except Exception as e:
            print(f"\nError: {str(e)}")
            print("Por favor, intenta de nuevo.")


if __name__ == "__main__":
    main()

