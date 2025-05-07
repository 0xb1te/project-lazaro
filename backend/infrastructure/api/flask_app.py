# src/infrastructure/api/flask_app.py
from typing import Dict, Any, Optional
import os
import uuid
import time
from datetime import datetime
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from werkzeug.utils import secure_filename
import json

from backend.infrastructure.config import Config
from backend.infrastructure.di.container import Container
from backend.application.dto.query_dto import QueryRequestDTO, QueryResponseDTO
from backend.application.dto.conversation_dto import ConversationDTO, MessageDTO, DocumentDTO
from backend.application.dto.document_dto import DocumentUploadRequestDTO, DocumentUploadResponseDTO
from backend.application.dto.file_analysis_dto import FileAnalysisRequestDTO, FileAnalysisResponseDTO, FileAnalysis, IndexDocumentDTO

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
        self.app.route("/health")(self.health_check)
        
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
        self.app.route("/conversations/<conversation_id>/documents/<document_id>", methods=["DELETE"])(self.delete_document)
        
        # File analysis routes
        self.app.route("/analyze", methods=["POST"])(self.analyze_file)
        self.app.route("/conversations/<conversation_id>/index", methods=["GET"])(self.get_index_document)
        
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
        ollama_status = "unknown"
        model_status = "unknown"
        
        try:
            # Verificar el estado del servicio de Ollama
            llm_service = self.container.get_llm_service()
            ollama_available = llm_service.check_model_availability()
            
            if ollama_available:
                ollama_status = "available"
                model_status = "loaded"
            else:
                # Intentar obtener información más detallada
                try:
                    # Verificar si el servidor Ollama está en ejecución
                    import requests
                    response = requests.get(self.config.OLLAMA_BASE_URL, timeout=2)
                    if response.status_code == 200:
                        ollama_status = "available"
                        model_status = "not_loaded"
                    else:
                        ollama_status = f"error: status {response.status_code}"
                except Exception as server_error:
                    ollama_status = f"unavailable: {str(server_error)}"
        except Exception as e:
            ollama_status = f"error: {str(e)}"
        
        env_config = {
            "status": "healthy",
            "environment": {
                "QDRANT_HOST": self.config.QDRANT_HOST,
                "QDRANT_PORT": self.config.QDRANT_PORT,
                "BASE_COLLECTION_NAME": self.config.BASE_COLLECTION_NAME,
                "USE_PER_CONVERSATION_COLLECTIONS": self.config.USE_PER_CONVERSATION_COLLECTIONS,
                "LLM_MODEL": self.config.LLM_MODEL,
                "OLLAMA_BASE_URL": self.config.OLLAMA_BASE_URL,
                "STORAGE_DIR": self.config.STORAGE_DIR,
                "UPLOAD_FOLDER": self.config.UPLOAD_FOLDER,
                "EMBEDDING_MODEL": self.config.EMBEDDING_MODEL,
                "DEBUG_MODE": self.config.DEBUG_MODE,
                "WORKING_DIRECTORY": os.getcwd(),
                "VERSION": "2.0.0"
            },
            "services": {
                "ollama": {
                    "status": ollama_status,
                    "model": self.config.LLM_MODEL,
                    "model_status": model_status
                }
            }
        }
        return jsonify(env_config)
    
    def get_all_conversations(self) -> Response:
        """Get all conversations."""
        conversation_service = self.container.get_conversation_service()
        conversations = conversation_service.get_all_conversations()
        
        # Convert to dictionary representation
        result = [conv.to_dict() for conv in conversations]
        
        # Añadir logging para debuggear
        print(f"Returning {len(result)} conversations")
        
        # Empaquetar en un objeto con propiedad 'conversations' para compat. con frontend
        return jsonify({"conversations": result})
    
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
                # Check if this message already exists in the conversation
                conversation = conversation_service.get_conversation(conversation_id)
                if conversation:
                    # Look for duplicate messages within the last 5 seconds
                    current_time = datetime.now()
                    for msg in reversed(conversation.messages):
                        if (msg.role == role and 
                            msg.content == content and 
                            (current_time - datetime.fromisoformat(msg.timestamp)).total_seconds() < 5):
                            # Return existing message if found
                            return jsonify({
                                "user_message": msg.to_dict(),
                                "assistant_message": None
                            })
                
                # Add the user message if no duplicate found
                message = conversation_service.add_user_message(conversation_id, content)
                
                if not message:
                    return jsonify({"error": "Conversation not found"}), 404
                
                # After adding user message, generate an AI response
                try:
                    # Create query request
                    query_service = self.container.get_query_service()
                    query_request = QueryRequestDTO(
                        query=content,
                        conversation_id=conversation_id,
                        max_results=5,
                        temperature=0.7,
                        include_context=True
                    )
                    
                    # Process the query to get AI response
                    result = query_service.process_query(query_request)
                    
                    # Add the AI response as an assistant message
                    assistant_message = conversation_service.add_assistant_message(
                        conversation_id=conversation_id,
                        content=result.response
                    )
                    
                    # Return both messages
                    return jsonify({
                        "user_message": message.to_dict(),
                        "assistant_message": assistant_message.to_dict()
                    })
                except Exception as e:
                    print(f"Error generating AI response: {str(e)}")
                    # Return just the user message if AI generation fails
                    return jsonify({
                        "user_message": message.to_dict(),
                        "error": f"Failed to generate AI response: {str(e)}"
                    })
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
            
            # Create storage/documents directory if it doesn't exist
            documents_dir = os.path.join(self.config.STORAGE_DIR, "documents")
            os.makedirs(documents_dir, exist_ok=True)
            
            # Save the file to the documents directory
            secure_filename_value = secure_filename(file.filename)
            file_path = os.path.join(documents_dir, secure_filename_value)
            file.save(file_path)
            
            # Create document upload request DTO with the file path
            upload_request = DocumentUploadRequestDTO(
                filename=secure_filename_value,
                conversation_id=conversation_id,
                file_path=file_path
            )
            
            # Process the upload
            document_service = self.container.get_document_service()
            result = document_service.upload_document(upload_request)
            
            return jsonify(result.to_dict()), 200
        except Exception as e:
            import traceback
            print(f"Error uploading document: {str(e)}")
            print(traceback.format_exc())
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
    
    def delete_document(self, conversation_id: str, document_id: str) -> Response:
        """Delete a document from a conversation."""
        try:
            conversation_service = self.container.get_conversation_service()
            vector_repository = self.container.get_vector_repository()
            
            # First remove document from conversation
            success = conversation_service.remove_document_from_conversation(conversation_id, document_id)
            
            if not success:
                return jsonify({"error": "Document or conversation not found"}), 404
            
            # Then remove document chunks from vector store
            # Search for all chunks with this document_id
            chunks = vector_repository.search_by_metadata(
                metadata_filter={"document_id": document_id},
                collection_name=self.config.COLLECTION_NAME
            )
            
            # If chunks were found, delete them
            if chunks:
                chunk_ids = [chunk["id"] for chunk in chunks]
                deleted_count = vector_repository.delete_documents(
                    document_ids=chunk_ids,
                    collection_name=self.config.COLLECTION_NAME
                )
                print(f"Deleted {deleted_count} document chunks from vector store for document {document_id}")
            
            return jsonify({
                "success": True, 
                "message": f"Document {document_id} deleted from conversation {conversation_id} and vector store"
            })
        except Exception as e:
            import traceback
            print(f"Error deleting document: {str(e)}")
            print(traceback.format_exc())
            return jsonify({"error": str(e)}), 500
    
    def analyze_file(self) -> Response:
        """Handle file analysis request."""
        try:
            data = request.get_json() or {}
            file_path = data.get("file_path")
            content = data.get("content")
            conversation_id = data.get("conversation_id")
            
            if not file_path or not content:
                return jsonify({"error": "File path and content are required"}), 400
            
            # Create analysis request
            analysis_request = FileAnalysisRequestDTO(
                file_path=file_path,
                content=content,
                conversation_id=conversation_id
            )
            
            # Get file analysis service
            file_analysis_service = self.container.get_file_analysis_service()
            
            # Analyze file
            analysis = file_analysis_service.analyze_file(
                file_path=analysis_request.file_path,
                content=analysis_request.content
            )
            
            # Convert to response DTO
            response = FileAnalysisResponseDTO(
                file_path=analysis.file_path,
                summary=analysis.summary,
                relationships=analysis.relationships,
                hierarchy=analysis.hierarchy,
                swot=analysis.swot,
                timestamp=analysis.timestamp.isoformat()
            )
            
            return jsonify(response.to_dict())
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    def get_index_document(self, conversation_id: str) -> Response:
        """Get the index document for a conversation."""
        try:
            # Get file analysis service
            file_analysis_service = self.container.get_file_analysis_service()
            
            # Get all analyses for the conversation
            vector_repository = self.container.get_vector_repository()
            analyses_data = vector_repository.search_by_metadata(
                metadata_filter={
                    "type": "analysis",
                    "conversation_id": conversation_id
                }
            )
            
            # Convert to FileAnalysis objects
            analyses = []
            for data in analyses_data:
                try:
                    analysis_dict = json.loads(data["content"])
                    analyses.append(FileAnalysis.from_dict(analysis_dict))
                except Exception as e:
                    print(f"Error parsing analysis: {str(e)}")
                    continue
            
            # Generate index document
            index_content = file_analysis_service.create_index_document(analyses)
            
            # Create index document DTO
            index_doc = IndexDocumentDTO(
                content=index_content,
                conversation_id=conversation_id
            )
            
            return jsonify(index_doc.to_dict())
        except Exception as e:
            return jsonify({"error": str(e)}), 500
