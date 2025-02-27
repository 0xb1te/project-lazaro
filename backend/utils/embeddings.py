from langchain_ollama import OllamaEmbeddings
import os
from ..config import OLLAMA_BASE_URL, LLM_MODEL

LLM_MODEL = os.getenv("LLM_MODEL")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL")

def get_embeddings():
    return OllamaEmbeddings(model=LLM_MODEL, base_url=OLLAMA_BASE_URL)