# backend/config.py

import os
from dotenv import load_dotenv

load_dotenv()

# Qdrant configuration
QDRANT_HOST = os.getenv("QDRANT_HOST")
QDRANT_PORT = int(os.getenv("QDRANT_PORT"))
COLLECTION_NAME = os.getenv("COLLECTION_NAME")
LLM_MODEL = os.getenv("LLM_MODEL")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL")