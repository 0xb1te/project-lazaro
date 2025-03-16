import os
from waitress import serve

# Import infrastructure components
from src.infrastructure.config import Config
from src.infrastructure.di.container import Container
from src.infrastructure.api.flask_app import FlaskApiAdapter

# Import application services for direct access if needed
from src.application.service.conversation_service import ConversationService
from src.application.service.document_service import DocumentService
from src.application.service.query_service import QueryService

# Import infrastructure implementations
from src.infrastructure.repository.file_conversation_repository import FileConversationRepository
from src.infrastructure.repository.qdrant_vector_repository import QdrantVectorRepository
from src.infrastructure.service.sentence_transformer_service import SentenceTransformerService
from src.infrastructure.service.ollama_service import OllamaService

def create_app():
    """
    Create and configure the application.
    
    Returns:
        Flask application instance
    """
    # Load configuration
    config = Config()
    
    # Create Flask adapter
    adapter = FlaskApiAdapter(config)
    
    # Return the Flask application
    return adapter.get_app()

if __name__ == "__main__":
    # Load configuration
    config = Config()
    
    # Create dependency injection container
    container = Container(config)
    
    # Log startup message
    print(f"Starting application in {'DEBUG' if config.DEBUG_MODE else 'PRODUCTION'} mode")
    print(f"Qdrant: {config.QDRANT_HOST}:{config.QDRANT_PORT}")
    print(f"LLM Model: {config.LLM_MODEL}")
    print(f"Embedding Model: {config.EMBEDDING_MODEL}")
    
    # Create Flask adapter
    adapter = FlaskApiAdapter(config)
    app = adapter.get_app()
    
    # Check if debug mode is enabled
    if config.DEBUG_MODE:
        # Run with Flask's built-in server (for development)
        adapter.run(debug=True)
    else:
        # Run with Waitress (for production)
        print("Starting Waitress server...")
        serve(
            app, 
            host='0.0.0.0', 
            port=5000,
            threads=6,
            url_scheme='http',
            max_request_body_size=100 * 1024 * 1024  # 100MB
        )
