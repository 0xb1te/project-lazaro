# src/infrastructure/api/flask_app.py
from typing import Dict, Any, Optional
import os
import uuid
import time
from datetime import datetime
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from werkzeug.utils import secure_filename

from src.infrastructure.config import Config
from src.infrastructure.di.container import Container
from src.application.dto.query_dto import QueryRequestDTO, QueryResponseDTO
from src.application.dto.conversation_dto import ConversationDTO, MessageDTO, DocumentDTO
from src.application.dto.document_dto import DocumentUploadRequestDTO, DocumentUploadResponseDTO

class FlaskApiAdapter:
    """
    Adapter for the Flask web framework to expose the application's functionality via HTTP.
    This class adapts the Flask HTTP interface to the application's interfaces.
    """
    
    def __init__(self, config: Config):
        """
        Initialize the Flask application with configuration and dependencies.
        
        Args:
            config: Application configuration
        """
        self.config = config
        self.container = Container(config)
        
        # Initialize Flask app
        self.app = Flask(__name__)
        CORS(self.app, resources={r"/*": {"origins": "*"}})
        
        # Configure file upload
        self.app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB in bytes
        
        # Setup routes
        self._setup_routes()
    
    def _setup_routes(self) -> None:
        """Set up the API routes."""
        # Health check
        self.app.route("/")(self.health_check)
        
        # Conversation routes
        self.app.route("/conversations", methods=["GET"])(self.get_all_conversations)
        self.app.route("/conversations", methods=["POST"])(self.create_conversation)
        self.app.route("/conversations/<conversation_id>", methods=["GET"])(self.get_conversation)
        self.app.route("/conversations/<conversation_id>", methods=["PUT"])(self.update_conversation)
        self.app.route("/conversations/<conversation_id>", methods=["DELETE"])(self.delete_conversation)
        self.app.route("/conversations/<conversation_id>/messages", methods=["POST"])(self.add_message)
        
        # Document routes
        self.app.route("/upload", methods=["POST"])(self.upload_document)
        self.app.route("/conversations/<conversation_id>/documents", methods=["GET"])(self.get_conversation_documents)
        
        # Query routes
        self.app.route("/ask", methods=["POST"])(self.ask_question)
        
        # Debug routes (only in debug mode)
        if self.config.DEBUG_MODE:
            self.app.route("/debug/collection", methods=["GET"])(self.debug_collection_info)
    
    def get_app(self) -> Flask:
        """
        Get the configured Flask application.
        
        Returns:
            Flask application instance
        """
        return self.app
    
    def run(self, **kwargs) -> None:
        """
        Run the Flask application.
        
        Args:
            **kwargs: Keyword arguments to pass to Flask's run method
        """
        self.app.run(**kwargs)
    
    # Route handlers
    
    def health_check(self) -> Response:
        """Health check endpoint."""
        env_config = {
            "status": "healthy",
            "environment": {
                "QDRANT_HOST": self.config.QDRANT_HOST,
                "QDRANT_PORT": self.config.QDRANT_PORT,
                "COLLECTION_NAME": self.config.COLLECTION_NAME,
                "LLM_MODEL": self.config.LLM_MODEL,
                "OLLAMA_BASE_URL": self.config.OLLAMA_BASE_URL,
                "STORAGE_DIR": self.config.STORAGE_DIR,
                "UPLOAD_FOLDER": self.config.UPLOAD_FOLDER,
                "EMBEDDING_MODEL": self.config.EMBEDDING_MODEL,
                "DEBUG_MODE": self.config.DEBUG_MODE,
                "WORKING_DIRECTORY": os.getcwd(),
                "VERSION": "2.0.0"
            }
        }
        return jsonify(env_config)
    
    def get_all_conversations(self) -> Response:
        """Get all conversations."""
        conversation_service = self.container.get_conversation_service()
        conversations = conversation_service.get_all_conversations()
        
        # Convert to dictionary representation
        result = [conv.to_dict() for conv in conversations]
        
        return jsonify(result)
    
    def create_conversation(self) -> Response:
        """Create a new conversation."""
        try:
            data = request.get_json() or {}
            title = data.get("title", "New Conversation")
            initial_message = data.get("initial_message")
            
            conversation_service = self.container.get_conversation_service()
            new_conversation = conversation_service.create_conversation(
                title=title,
                initial_message=initial_message
            )
            
            return jsonify(new_conversation.to_dict()), 201
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    def get_conversation(self, conversation_id: str) -> Response:
        """Get a single conversation by ID."""
        conversation_service = self.container.get_conversation_service()
        conversation = conversation_service.get_conversation(conversation_id)
        
        if not conversation:
            return jsonify({"error": "Conversation not found"}), 404
        
        return jsonify(conversation.to_dict())
    
    def update_conversation(self, conversation_id: str) -> Response:
        """Update a conversation."""
        try:
            data = request.get_json() or {}
            title = data.get("title")
            
            if not title:
                return jsonify({"error": "Title is required"}), 400
            
            conversation_service = self.container.get_conversation_service()
            updated_conversation = conversation_service.update_conversation_title(
                conversation_id=conversation_id,
                title=title
            )
            
            if not updated_conversation:
                return jsonify({"error": "Conversation not found"}), 404
            
            return jsonify(updated_conversation.to_dict())
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    def delete_conversation(self, conversation_id: str) -> Response:
        """Delete a conversation."""
        conversation_service = self.container.get_conversation_service()
        success = conversation_service.delete_conversation(conversation_id)
        
        if not success:
            return jsonify({"error": "Conversation not found"}), 404
        
        return jsonify({"success": True, "message": "Conversation deleted"})
    
    def add_message(self, conversation_id: str) -> Response:
        """Add a message to a conversation."""
        try:
            data = request.get_json() or {}
            role = data.get("role")
            content = data.get("content")
            
            if not role or not content:
                return jsonify({"error": "Role and content are required"}), 400
            
            conversation_service = self.container.get_conversation_service()
            
            # Use the appropriate method based on role
            if role == "user":
                message = conversation_service.add_user_message(conversation_id, content)
            elif role == "assistant":
                message = conversation_service.add_assistant_message(conversation_id, content)
            elif role == "system":
                message = conversation_service.add_system_message(conversation_id, content)
            else:
                return jsonify({"error": "Invalid role. Must be 'user', 'assistant', or 'system'"}), 400
            
            if not message:
                return jsonify({"error": "Conversation not found"}), 404
            
            return jsonify(message.to_dict())
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    def upload_document(self) -> Response:
        """Handle document upload."""
        try:
            if "file" not in request.files:
                return jsonify({"error": "No file uploaded"}), 400
            
            file = request.files["file"]
            if file.filename == "":
                return jsonify({"error": "No file selected"}), 400
            
            # Get conversation ID from request (optional)
            conversation_id = request.form.get("conversation_id")
            
            # Create document upload request DTO
            upload_request = DocumentUploadRequestDTO(
                file=file,
                filename=secure_filename(file.filename),
                conversation_id=conversation_id
            )
            
            # Process the upload
            document_service = self.container.get_document_service()
            result = document_service.upload_document(upload_request)
            
            return jsonify(result.to_dict()), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    def get_conversation_documents(self, conversation_id: str) -> Response:
        """Get documents associated with a conversation."""
        conversation_service = self.container.get_conversation_service()
        documents = conversation_service.get_conversation_documents(conversation_id)
        
        if documents is None:
            return jsonify({"error": "Conversation not found"}), 404
        
        result = [doc.to_dict() for doc in documents]
        return jsonify(result)
    
    def ask_question(self) -> Response:
        """Handle a question/query request."""
        try:
            start_time = time.time()
            data = request.get_json() or {}
            
            # Required fields
            query = data.get("query")
            if not query:
                return jsonify({"error": "Query is required"}), 400
            
            # Optional fields with defaults
            conversation_id = data.get("conversation_id")
            max_results = data.get("max_results", 5)
            temperature = data.get("temperature", 0.7)
            include_context = data.get("include_context", True)
            
            # Create query request DTO
            query_request = QueryRequestDTO(
                query=query,
                conversation_id=conversation_id,
                max_results=max_results,
                temperature=temperature,
                include_context=include_context
            )
            
            # Process the query
            query_service = self.container.get_query_service()
            result = query_service.process_query(query_request)
            
            # Add processing time
            processing_time = (time.time() - start_time) * 1000  # ms
            response_dict = result.to_dict()
            response_dict["processing_time_ms"] = processing_time
            
            return jsonify(response_dict)
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    def debug_collection_info(self) -> Response:
        """Debug endpoint to get vector collection info."""
        if not self.config.DEBUG_MODE:
            return jsonify({"error": "Debug mode is disabled"}), 403
        
        try:
            vector_repository = self.container.get_vector_repository()
            info = vector_repository.get_collection_info()
            return jsonify(info)
        except Exception as e:
            return jsonify({"error": str(e)}), 500