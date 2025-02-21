from langchain_ollama import OllamaEmbeddings
import os

LLM_MODEL = os.getenv("LLM_MODEL")

def get_embeddings():
    return OllamaEmbeddings(model=LLM_MODEL, base_url="http://localhost:11434")