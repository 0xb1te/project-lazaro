# src/infrastructure/config.py
import os
from typing import Dict, Any
from dotenv import load_dotenv

class Config:
    """
    Configuration class for the application.
    Loads configuration from environment variables with sensible defaults.
    """
    
    def __init__(self):
        """
        Initialize configuration from environment variables.
        
        Loads variables from .env file if present and sets default values
        for missing variables.
        """
        # Try to load environment variables from .env file
        load_dotenv()
        
        # Vector database configuration
        self.QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
        self.QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
        self.COLLECTION_NAME = os.getenv("COLLECTION_NAME", "documents")
        self.CONVERSATIONS_COLLECTION = os.getenv("CONVERSATIONS_COLLECTION", "conversations")
        self.EMBEDDING_DIMENSION = int(os.getenv("EMBEDDING_DIMENSION", "384"))
        
        # LLM configuration
        self.LLM_MODEL = os.getenv("LLM_MODEL", "llama2")
        self.OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
        self.TEMPERATURE = float(os.getenv("TEMPERATURE", "0.7"))
        self.MAX_CONTEXT_LENGTH = int(os.getenv("MAX_CONTEXT_LENGTH", "4096"))
        self.MAX_HISTORY_MESSAGES = int(os.getenv("MAX_HISTORY_MESSAGES", "10"))
        self.CONVERSATION_AWARE = os.getenv("CONVERSATION_AWARE", "True").lower() == "true"
        
        # Embedding model configuration
        self.EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
        
        # Storage configuration
        current_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.STORAGE_DIR = os.getenv("STORAGE_DIR", os.path.join(current_dir, "storage"))
        self.UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", os.path.join(self.STORAGE_DIR, "documents"))
        
        # Ensure directories exist
        os.makedirs(self.STORAGE_DIR, exist_ok=True)
        os.makedirs(self.UPLOAD_FOLDER, exist_ok=True)
        
        # Application configuration
        self.DEBUG_MODE = os.getenv("DEBUG_MODE", "False").lower() == "true"
        self.LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
        self.API_PORT = int(os.getenv("API_PORT", "5000"))
        self.API_HOST = os.getenv("API_HOST", "0.0.0.0")
        
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert configuration to a dictionary.
        
        Returns:
            Dictionary with all configuration values
        """
        return {
            "qdrant": {
                "host": self.QDRANT_HOST,
                "port": self.QDRANT_PORT,
                "collection_name": self.COLLECTION_NAME,
                "conversations_collection": self.CONVERSATIONS_COLLECTION,
                "embedding_dimension": self.EMBEDDING_DIMENSION
            },
            "llm": {
                "model": self.LLM_MODEL,
                "ollama_base_url": self.OLLAMA_BASE_URL,
                "temperature": self.TEMPERATURE,
                "max_context_length": self.MAX_CONTEXT_LENGTH,
                "max_history_messages": self.MAX_HISTORY_MESSAGES,
                "conversation_aware": self.CONVERSATION_AWARE
            },
            "embedding": {
                "model": self.EMBEDDING_MODEL
            },
            "storage": {
                "storage_dir": self.STORAGE_DIR,
                "upload_folder": self.UPLOAD_FOLDER
            },
            "app": {
                "debug_mode": self.DEBUG_MODE,
                "log_level": self.LOG_LEVEL,
                "api_port": self.API_PORT,
                "api_host": self.API_HOST
            }
        }
