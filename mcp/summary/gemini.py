"""
Client for the Google Gemini API.
Handles connection, errors and retry logic.
"""
import os
import time
from typing import Optional
import google.generativeai as genai
from .config import GeminiConfig


class GeminiClient:
    """Client for interacting with the Gemini API."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initializes the Gemini client.
        
        Args:
            api_key: Gemini API key. If not provided, reads from GEMINI_API_KEY
        """
        from .config import ServiceConfig
        api_key = api_key or ServiceConfig.GEMINI_API_KEY
        if not api_key:
            raise ValueError("GEMINI_API_KEY not configured in environment variables")
        
        genai.configure(api_key=api_key)
        
        safety_settings = GeminiConfig.get_safety_settings()
        generation_config = GeminiConfig.get_generation_config()
        
        self.model = genai.GenerativeModel(
            model_name=GeminiConfig.MODEL_NAME,
            safety_settings=safety_settings,
            generation_config=generation_config
        )
    
    def generate_content(self, prompt: str, max_retries: Optional[int] = None) -> str:
        """
        Generates content using Gemini with error handling and retry.
        
        Args:
            prompt: Prompt to send to Gemini
            max_retries: Maximum number of retries
            
        Returns:
            Text of the Gemini response
            
        Raises:
            ValueError: If there is an error in the API after all retries
        """
        max_retries = max_retries or GeminiConfig.MAX_RETRIES
        last_error = None
        
        for attempt in range(max_retries):
            try:
                response = self.model.generate_content(prompt)
                
                if not response.text:
                    raise ValueError("Empty response from Gemini")
                
                return response.text
            
            except Exception as e:
                last_error = e
                error_str = str(e).lower()
                
                if "api key" in error_str or "authentication" in error_str:
                    raise ValueError(f"Authentication error with Gemini: {str(e)}")
                
                if "quota" in error_str or "rate limit" in error_str:
                    wait_time = (attempt + 1) * GeminiConfig.RETRY_QUOTA_BACKOFF
                    if attempt < max_retries - 1:
                        time.sleep(wait_time)
                        continue
                    raise ValueError(f"Gemini quota limit exceeded: {str(e)}")
                
                if "safety" in error_str or "blocked" in error_str:
                    raise ValueError(f"Content blocked by security policies: {str(e)}")
                
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * GeminiConfig.RETRY_BACKOFF_BASE
                    time.sleep(wait_time)
                    continue
                else:
                    raise ValueError(f"Error generating content with Gemini (attempts exhausted): {str(e)}")
        
        raise ValueError(f"Error generating content: {str(last_error)}")
    
    def is_available(self) -> bool:
        """
        Checks if the client is available and configured correctly.
        
        Returns:
            True if the client is available
        """
        try:
            test_response = self.model.generate_content("test")
            return test_response.text is not None
        except Exception:
            return False

