#!/usr/bin/env python3
"""
Simple script to verify environment variables are properly loaded.
Run this script to debug environment variable issues.
"""

import os
from dotenv import load_dotenv
import sys

def check_env_vars():
    """Check if environment variables are properly loaded and print their values."""
    # Check if .env file exists
    env_exists = os.path.exists('.env')
    print(f".env file exists: {env_exists}")
    
    if env_exists:
        print("\nContents of .env file:")
        with open('.env', 'r') as f:
            print(f.read())
    
    # Load environment variables
    load_dotenv()
    
    # List of variables to check
    env_vars = [
        "QDRANT_HOST",
        "QDRANT_PORT",
        "COLLECTION_NAME",
        "CONVERSATIONS_COLLECTION",
        "LLM_MODEL",
        "OLLAMA_BASE_URL",
        "STORAGE_DIR",
        "UPLOAD_FOLDER",
        "EMBEDDING_MODEL",
        "EMBEDDING_DIMENSION",
        "DEBUG_MODE"
    ]
    
    print("\nEnvironment Variables:")
    for var in env_vars:
        value = os.getenv(var)
        print(f"{var}: {value if value is not None else 'Not set'}")
    
    # Print environment for debugging
    print("\nFull Environment Variables:")
    for key, value in sorted(os.environ.items()):
        print(f"{key}: {value}")

if __name__ == "__main__":
    print(f"Python version: {sys.version}")
    print(f"Current working directory: {os.getcwd()}")
    check_env_vars()