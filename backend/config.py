import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Qdrant configuration
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "ai-rag-project")
CONVERSATIONS_COLLECTION = os.getenv("CONVERSATIONS_COLLECTION", "conversations")

# LLM configuration
LLM_MODEL = os.getenv("LLM_MODEL", "hf.co/bartowski/DeepSeek-Coder-V2-Lite-Instruct-GGUF:Q8_0_L")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://172.17.0.1:11434")

# Storage configuration
STORAGE_DIR = os.getenv("STORAGE_DIR", "./storage")
UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "./uploads")

# Ensure required directories exist
os.makedirs(STORAGE_DIR, exist_ok=True)
os.makedirs(os.path.join(STORAGE_DIR, "conversations"), exist_ok=True)
os.makedirs(os.path.join(STORAGE_DIR, "documents"), exist_ok=True)
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Embedding model configuration
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
EMBEDDING_DIMENSION = int(os.getenv("EMBEDDING_DIMENSION", "384"))
TEMPERATURE = float(os.getenv("EMBEDDING_TEMPERATURE", 0.4))

# Application settings
DEBUG_MODE = os.getenv("DEBUG_MODE", "False").lower() == "true"

# Conversation settings
MAX_HISTORY_MESSAGES = int(os.getenv("MAX_HISTORY_MESSAGES", "15"))  # Number of previous messages to include
MAX_CONTEXT_LENGTH = int(os.getenv("MAX_CONTEXT_LENGTH", "4096"))  # Max tokens for LLM context
CONVERSATION_AWARE = os.getenv("CONVERSATION_AWARE", "True").lower() == "true"  # Enable/disable conversation history