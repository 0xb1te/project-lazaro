"""
Backend package for the Ollama Qdrant Vector Search application.
This package provides functionality for file processing, vector database handling,
and embeddings generation using Ollama and Qdrant.
"""

from .utils.qdrant_handler import (
    get_qdrant_client,
    init_collection,
    insert_documents,
    search_similar_documents,
    clear_collection
)
from .utils.file_processor import process_file, process_zip_file
from .utils.embeddings import get_embeddings
from .config import QDRANT_HOST, QDRANT_PORT, COLLECTION_NAME, LLM_MODEL

__version__ = "0.1"

__all__ = [
    'get_qdrant_client',
    'init_collection',
    'insert_documents',
    'search_similar_documents',
    'clear_collection',
    'process_file',
    'process_zip_file',
    'get_embeddings',
    'QDRANT_HOST',
    'QDRANT_PORT',
    'COLLECTION_NAME',
    'LLM_MODEL'
]