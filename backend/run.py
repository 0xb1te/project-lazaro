"""
Entry point for the application.
Initializes the dependency injection container, 
configures the application and starts the server.
"""

import os
import sys
import logging
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

def setup_logging(config: Config) -> None:
    """
    Set up application logging based on configuration.
    
    Args:
        config: Application configuration
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
    
    # Create formatter
    formatter = logging.getLogger()
    console_handler.setFormatter(formatter)
    
    # Add handlers
    logger.addHandler(console_handler)
    
    return logger

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
