"""
LLM Configuration Module
Loads credentials from .env file and initializes Google LLM connections
"""
import os
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables from .env file
load_dotenv()

class LLMConfig:
    """Configuration class for Google LLM connections"""
    
    def __init__(self):
        """Initialize LLM configuration from environment variables"""
        self.api_key = os.getenv('GOOGLE_API_KEY')
        self.model_name = os.getenv('GEMINI_MODEL', 'gemini-1.5-pro')
        self.temperature = float(os.getenv('GEMINI_TEMPERATURE', '0.2'))
        self.project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        self.region = os.getenv('GOOGLE_CLOUD_REGION', 'us-central1')
        
        if not self.api_key:
            raise ValueError(
                "GOOGLE_API_KEY not found in .env file. "
                "Please create a .env file with your Google API key. "
                "See .env.example for reference."
            )
        
        # Configure Google Generative AI
        genai.configure(api_key=self.api_key)
        
    def get_model(self, model_name=None, temperature=None):
        """
        Get a configured Google Generative AI model
        
        Args:
            model_name: Optional model name override (default: from config)
            temperature: Optional temperature override (default: from config)
            
        Returns:
            Configured GenerativeModel instance
        """
        model = model_name or self.model_name
        temp = temperature if temperature is not None else self.temperature
        
        return genai.GenerativeModel(
            model_name=model,
            generation_config={
                'temperature': temp,
            }
        )
    
    def get_chat_model(self, model_name=None, temperature=None):
        """
        Get a model configured for chat/conversation
        
        Args:
            model_name: Optional model name override
            temperature: Optional temperature override
            
        Returns:
            Configured GenerativeModel instance
        """
        return self.get_model(model_name, temperature)

# Global instance
_llm_config = None

def get_llm_config():
    """Get or create the global LLM configuration instance"""
    global _llm_config
    if _llm_config is None:
        _llm_config = LLMConfig()
    return _llm_config

def get_model(model_name=None, temperature=None):
    """Convenience function to get a configured model"""
    config = get_llm_config()
    return config.get_model(model_name, temperature)

