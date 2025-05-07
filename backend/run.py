"""
Entry point for the application.
Initializes the dependency injection container, 
configures the application and starts the server.
"""

import os
import sys
import logging
import subprocess
import time
import requests
from waitress import serve

# Add the root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import infrastructure components
from backend.infrastructure.config import Config
from backend.infrastructure.di.container import Container
from backend.infrastructure.api.flask_app import FlaskApiAdapter

# Import application services for direct access if needed
from backend.application.service.conversation_service import ConversationService
from backend.application.service.document_service import DocumentService
from backend.application.service.query_service import QueryService

# Import infrastructure implementations
from backend.infrastructure.repository.file_conversation_repository import FileConversationRepository
from backend.infrastructure.repository.qdrant_vector_repository import QdrantVectorRepository
from backend.infrastructure.service.sentence_transformer_service import SentenceTransformerService
from backend.infrastructure.service.ollama_service import OllamaService

def setup_logging(config: Config) -> logging.Logger:
    """
    Set up application logging based on configuration.
    
    Args:
        config: Application configuration
        
    Returns:
        Logger instance
    """
    log_level = getattr(logging, config.LOG_LEVEL, logging.INFO)
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create logger
    logger = logging.getLogger('project_lazaro')
    logger.setLevel(log_level)
    
    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    
    # Create formatter (important change - use Formatter, not Logger)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    
    # Add handlers
    logger.addHandler(console_handler)
    
    return logger

def check_and_pull_ollama_model(config: Config, logger: logging.Logger) -> bool:
    """
    Check if the configured Ollama model is available and pull it if not.
    
    Args:
        config: Application configuration
        logger: Logger instance
        
    Returns:
        True if the model is available or was successfully pulled, False otherwise
    """
    model_name = config.LLM_MODEL
    ollama_url = config.OLLAMA_BASE_URL
    
    logger.info(f"Checking if Ollama model '{model_name}' is available at {ollama_url}")
    
    try:
        # Check if Ollama server is running
        try:
            response = requests.get(f"{ollama_url}/", timeout=5)
            if response.status_code != 200:
                logger.warning(f"Ollama server returned status code {response.status_code}")
        except requests.exceptions.ConnectionError:
            logger.error(f"Could not connect to Ollama server at {ollama_url}")
            logger.info("Make sure Ollama is running before starting the server")
            return False
        
        # Check if the model is already available
        try:
            # List models using Ollama API
            list_response = requests.get(f"{ollama_url}/api/tags", timeout=10)
            if list_response.status_code == 200:
                models_data = list_response.json()
                
                # Handle different API response formats
                if "models" in models_data:
                    models = models_data.get("models", [])
                    model_names = [model.get("name") for model in models]
                else:
                    # Newer Ollama API format
                    models = models_data.get("models", [])
                    if not models and isinstance(models_data, list):
                        # Fallback to direct array
                        models = models_data
                    model_names = [model.get("name") for model in models]
                
                logger.info(f"Available models: {model_names}")
                
                if model_name in model_names:
                    logger.info(f"Model '{model_name}' is already available")
                    return True
                
                # Model not found, need to pull it
                logger.info(f"Model '{model_name}' not found, attempting to pull...")
            else:
                logger.warning(f"Failed to list models: {list_response.status_code}")
                # If we can't list models, we'll attempt to pull anyway
                logger.info(f"Attempting to pull model '{model_name}'...")
        except Exception as e:
            logger.warning(f"Error checking available models: {str(e)}")
            logger.info(f"Attempting to pull model '{model_name}' anyway...")
        
        # Try to pull the model
        print(f"\n=== Pulling model {model_name} - this may take several minutes on first download ===\n")
        
        # First try using API
        try:
            pull_response = requests.post(
                f"{ollama_url}/api/pull",
                json={"name": model_name},
                timeout=600  # 10 minutes timeout
            )
            
            if pull_response.status_code == 200:
                logger.info(f"Successfully pulled model '{model_name}' via API")
                return True
        except Exception as api_error:
            logger.warning(f"Error pulling model via API: {str(api_error)}")
        
        # If API call fails, try using CLI
        try:
            logger.info(f"Attempting to pull model '{model_name}' via CLI...")
            result = subprocess.run(
                ["ollama", "pull", model_name],
                capture_output=True,
                text=True,
                timeout=600  # 10 minutes timeout
            )
            
            if result.returncode == 0:
                logger.info(f"Successfully pulled model '{model_name}' via CLI")
                return True
            else:
                logger.error(f"Failed to pull model '{model_name}' via CLI: {result.stderr}")
                return False
        except Exception as cli_error:
            logger.error(f"Error pulling model via CLI: {str(cli_error)}")
            return False
            
    except Exception as e:
        logger.error(f"Unexpected error checking/pulling Ollama model: {str(e)}")
        return False
        
    return False  # Default return if we reach end without success

def create_app():
    """
    Create and configure the application.
    
    Returns:
        Flask application instance
    """
    # Load configuration
    config = Config()
    
    # Set up logging
    setup_logging(config)
    
    # Create Flask adapter
    adapter = FlaskApiAdapter(config)
    
    # Return the Flask application
    return adapter.get_app()

def main():
    """
    Main entry point for the application.
    Initializes the application and starts the server.
    """
    # Load configuration
    config = Config()
    
    # Set up logging
    logger = setup_logging(config)
    
    # Check and pull Ollama model if needed
    logger.info("Checking Ollama model availability...")
    model_available = check_and_pull_ollama_model(config, logger)
    
    if not model_available:
        logger.warning(f"Could not verify or pull model '{config.LLM_MODEL}'. The application will still start, but AI responses may fail until the model is available.")
    
    # Create dependency injection container
    container = Container(config)
    
    # Log startup message
    logger.info(f"Starting application in {'DEBUG' if config.DEBUG_MODE else 'PRODUCTION'} mode")
    logger.info(f"Qdrant: {config.QDRANT_HOST}:{config.QDRANT_PORT}")
    logger.info(f"LLM Model: {config.LLM_MODEL}")
    logger.info(f"Embedding Model: {config.EMBEDDING_MODEL}")
    
    # Create Flask adapter
    adapter = FlaskApiAdapter(config)
    app = adapter.get_app()
    
    # Check if debug mode is enabled
    if config.DEBUG_MODE:
        # Run with Flask's built-in server (for development)
        logger.info("Starting Flask development server...")
        adapter.run(
            host=config.API_HOST, 
            port=config.API_PORT, 
            debug=True
        )
    else:
        # Run with Waitress (for production)
        logger.info("Starting Waitress production server...")
        serve(
            app, 
            host=config.API_HOST, 
            port=config.API_PORT,
            threads=6,
            url_scheme='http',
            max_request_body_size=100 * 1024 * 1024  # 100MB
        )

if __name__ == "__main__":
    main()
