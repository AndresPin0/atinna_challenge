"""Streamlit interface for the conversational agent."""
import sys
import os
from pathlib import Path

# Add parent directory to path to import agent modules
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import streamlit as st
from dotenv import load_dotenv
from agent.config import AgentConfig
from agent.gemini import GeminiClient
from agent.graph import create_agent_graph
from agent.memory import AgentState
from agent.graph import state_to_dict, dict_to_state


# Load environment variables
load_dotenv()


def initialize_agent():
    """Initialize the agent graph and return it."""
    if 'agent_graph' not in st.session_state:
        try:
            AgentConfig.validate()
        except ValueError as e:
            st.error(f"Error de configuración: {e}")
            st.info("Asegúrate de tener GEMINI_API_KEY en tu archivo .env")
            st.stop()
        
        try:
            gemini_client = GeminiClient()
            graph = create_agent_graph(gemini_client)
            st.session_state.agent_graph = graph
            st.session_state.agent_initialized = True
        except Exception as e:
            st.error(f"Error inicializando Gemini: {e}")
            st.stop()
    
    return st.session_state.agent_graph


def initialize_state():
    """Initialize the persistent agent state."""
    if 'agent_state' not in st.session_state:
        st.session_state.agent_state = AgentState(user_query="")


def main():
    """Main Streamlit application."""
    st.set_page_config(
        page_title="Agente Conversacional - Reto Atinna",
        page_icon="",
        layout="wide"
    )
    
    # Initialize agent and state
    initialize_state()
    graph = initialize_agent()
    
    # Title and description
    st.title("Agente Conversacional")
    st.markdown("Sistema de análisis conversacional con IA generativa")
    st.markdown("---")
    
    # Sidebar with info
    with st.sidebar:
        st.header("Información")
        st.markdown("""
        **Capacidades del Agente:**
        - Resumen ejecutivo de conversaciones
        - Análisis de sentimiento y clima emocional
        - Análisis de propagación y viralidad
        
        **Instrucciones:**
        - Escribe tu consulta en el campo de abajo
        - El agente decidirá automáticamente qué análisis realizar
        - Puedes hacer preguntas de seguimiento sin repetir información
        """)
        
        if st.session_state.agent_state.current_thread_id:
            st.info(f"**Thread actual:** {st.session_state.agent_state.current_thread_id}")
        
        if st.session_state.agent_state.last_analysis:
            st.success("Último análisis guardado en memoria")
        
        if st.button("Limpiar Conversación"):
            st.session_state.agent_state = AgentState(user_query="")
            st.session_state.messages = []
            st.rerun()
    
    # Initialize messages in session state
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    
    # Display conversation history
    chat_container = st.container()
    with chat_container:
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
    
    # User input
    if prompt := st.chat_input("Escribe tu consulta aquí..."):
        # Add user message to chat
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Process with agent
        with st.chat_message("assistant"):
            with st.spinner("Procesando..."):
                try:
                    # Prepare current state
                    current_state = AgentState(user_query=prompt)
                    
                    # Copy conversation history from persistent state
                    for msg in st.session_state.agent_state.conversation_history:
                        current_state.conversation_history.append(msg)
                    
                    # Copy last analysis and thread ID
                    current_state.last_analysis = st.session_state.agent_state.last_analysis
                    current_state.current_thread_id = st.session_state.agent_state.current_thread_id
                    
                    # Convert to graph state
                    graph_state = state_to_dict(current_state)
                    
                    # Invoke graph
                    final_graph_state = graph.invoke(graph_state)
                    
                    # Convert back to agent state
                    final_state = dict_to_state(final_graph_state)
                    
                    # Update persistent state
                    st.session_state.agent_state = final_state
                    
                    # Display response
                    response = final_state.final_response
                    st.markdown(response)
                    
                    # Add assistant message to chat
                    st.session_state.messages.append({"role": "assistant", "content": response})
                    
                except Exception as e:
                    error_msg = f"Error: {str(e)}\n\nPor favor, intenta de nuevo."
                    st.error(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})


if __name__ == "__main__":
    main()

