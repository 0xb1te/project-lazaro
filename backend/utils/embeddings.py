from langchain_ollama import OllamaEmbeddings
import logging
from ..config import OLLAMA_BASE_URL, LLM_MODEL, TEMPERATURE

# Configure logging
logger = logging.getLogger(__name__)

def get_embeddings():
    """
    Return Ollama embeddings instance using configuration from environment variables.
    """
    logger.info(f"Initializing embeddings with model: {LLM_MODEL}, base_url: {OLLAMA_BASE_URL}")
    return OllamaEmbeddings(model=LLM_MODEL, base_url=OLLAMA_BASE_URL, temperature=TEMPERATURE)