# src/infrastructure/config.py
import os
from dotenv import load_dotenv

class Config:
    """
    Configuration class for the application.
    Loads settings from environment variables.
    """
    
    def __init__(self):
        """Initialize configuration by loading from environment variables."""
        # Load environment variables from .env file
        load_dotenv()
        
        # Qdrant configuration
        self.QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
        self.QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
        self.COLLECTION_NAME = os.getenv("COLLECTION_NAME", "ai-rag-project")
        self.CONVERSATIONS_COLLECTION = os.getenv("CONVERSATIONS_COLLECTION", "conversations")
        
        # LLM configuration
        self.LLM_MODEL = os.getenv("LLM_MODEL", "hf.co/bartowski/DeepSeek-Coder-V2-Lite-Instruct-GGUF:Q8_0_L")
        self.OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://172.17.0.1:11434")
        
        # Storage configuration
        self.STORAGE_DIR = os.getenv("STORAGE_DIR", "./storage")
        self.UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "./uploads")
        
        # Ensure required directories exist
        self._create_directories()
        
        # Embedding model configuration
        self.EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
        self.EMBEDDING_DIMENSION = int(os.getenv("EMBEDDING_DIMENSION", "384"))
        self.TEMPERATURE = float(os.getenv("TEMPERATURE", "0.4"))
        
        # Application settings
        self.DEBUG_MODE = os.getenv("DEBUG_MODE", "False").lower() == "true"
        
        # Conversation settings
        self.MAX_HISTORY_MESSAGES = int(os.getenv("MAX_HISTORY_MESSAGES", "15"))
        self.MAX_CONTEXT_LENGTH = int(os.getenv("MAX_CONTEXT_LENGTH", "4096"))
        self.CONVERSATION_AWARE = os.getenv("CONVERSATION_AWARE", "True").lower() == "true"
    
    def _create_directories(self):
        """Create necessary directories if they don't exist."""
        os.makedirs(self.STORAGE_DIR, exist_ok=True)
        os.makedirs(os.path.join(self.STORAGE_DIR, "conversations"), exist_ok=True)
        os.makedirs(os.path.join(self.STORAGE_DIR, "documents"), exist_ok=True)
        os.makedirs(self.UPLOAD_FOLDER, exist_ok=True)
    
    def to_dict(self):
        """Convert configuration to dictionary."""
        return {
            "QDRANT_HOST": self.QDRANT_HOST,
            "QDRANT_PORT": self.QDRANT_PORT,
            "COLLECTION_NAME": self.COLLECTION_NAME,
            "CONVERSATIONS_COLLECTION": self.CONVERSATIONS_COLLECTION,
            "LLM_MODEL": self.LLM_MODEL,
            "OLLAMA_BASE_URL": self.OLLAMA_BASE_URL,
            "STORAGE_DIR": self.STORAGE_DIR,
            "UPLOAD_FOLDER": self.UPLOAD_FOLDER,
            "EMBEDDING_MODEL": self.EMBEDDING_MODEL,
            "EMBEDDING_DIMENSION": self.EMBEDDING_DIMENSION,
            "TEMPERATURE": self.TEMPERATURE,
            "DEBUG_MODE": self.DEBUG_MODE,
            "MAX_HISTORY_MESSAGES": self.MAX_HISTORY_MESSAGES,
            "MAX_CONTEXT_LENGTH": self.MAX_CONTEXT_LENGTH,
            "CONVERSATION_AWARE": self.CONVERSATION_AWARE
        }