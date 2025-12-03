"""Configuration for the agent and MCP endpoints."""
import os
from typing import Optional


class AgentConfig:
    """Configuration for the conversational agent."""
    
    # Agent Settings
    MAX_RETRIES: int = 3
    REQUEST_TIMEOUT: int = 30
    
    @classmethod
    def get_mcp_resumen_url(cls) -> str:
        """Get MCP Resumen URL from environment."""
        return os.getenv(
            "MCP_RESUMEN_URL", 
            "http://localhost:8000/analisis/resumen"
        )
    
    @classmethod
    def get_gemini_api_key(cls) -> Optional[str]:
        """Get Gemini API key from environment."""
        return os.getenv("GEMINI_API_KEY")
    
    @classmethod
    def get_gemini_model(cls) -> str:
        """Get Gemini model from environment."""
        return os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
    
    @classmethod
    def validate(cls) -> None:
        """Validates that required configuration is present."""
        api_key = cls.get_gemini_api_key()
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")

