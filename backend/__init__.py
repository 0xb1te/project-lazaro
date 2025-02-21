"""
Backend package for the Ollama Mongo DB Vector Search application.
This package provides functionality for file processing, database handling,
and embeddings generation using Ollama and MongoDB.
"""

from .utils.db_handler import get_db_collection
from .utils.file_processor import process_file, process_zip_file
from .utils.embeddings import get_embeddings
from .config import MONGO_URI, DB_NAME, COLLECTION_NAME, LLM_MODEL

__version__ = "0.1"

__all__ = [
    'get_db_collection',
    'process_file',
    'process_zip_file',
    'get_embeddings',
    'MONGO_URI',
    'DB_NAME',
    'COLLECTION_NAME',
    'LLM_MODEL'
]