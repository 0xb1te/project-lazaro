# src/infrastructure/api/flask_app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
import os

from src.infrastructure.config import Config
from src.infrastructure.di.container import Container
from src.application.service.conversation_service import ConversationService
from src.application.service.document_service import DocumentService
from src.application.service.query_service import QueryService

class FlaskApiAdapter:
    """
    Flask adapter for exposing application services through a REST API.
    This adapter connects the outside world (HTTP requests) to the application layer.
    """
    
    def __init__(self, config: Config):
        """
        Initialize the adapter with configuration and container.
        
        Args:
            config: Application configuration
        """
        self.config = config
        
        # Create dependency injection container
        self.container = Container(config)
        
        # Get services from the container
        self.conversation_service = self.container.conversation_service()
        self.document_service = self.container.document_service()
        self.query_service = self.container.query_service()
        
        # Initialize Flask app
        self.app = Flask(__name__)
        
        # Enable CORS
        CORS(self.app, resources={r"/*": {"origins": "*"}})
        
        # Set maximum content length (100MB)
        self.app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024
        
        # Initialize directories
        os.makedirs(config.UPLOAD_FOLDER, exist_ok=True)
        
        # Register routes
        self._register_routes()
    
    def _register_routes(self):
        """Register all API routes."""
        # Health check
        @self.app.route("/")
        def health_check():
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
                    "WORKING_DIRECTORY": os.getcwd(),
                    "ENV_FILE_EXISTS": os.path.exists('.env')
                },
                "version": "1.0.0"
            }
            
            return jsonify(env_config), 200
        
        # Error handlers
        @self.app.errorhandler(413)
        def request_entity_too_large(error):
            """Handle too large files."""
            return jsonify({
                "error": "The file is too large. Maximum allowed size is 100MB."
            }), 413
        
        # Document upload
        @self.app.route("/upload", methods=["POST"])
        def upload_file():
            """Upload and process a file."""
            try:
                if "file" not in request.files:
                    return jsonify({"error": "No file uploaded"}), 400
                
                file = request.files["file"]
                if file.filename == "":
                    return jsonify({"error": "No file selected"}), 400
                
                # Get conversation ID from request (optional)
                conversation_id = request.form.get("conversation_id")
                
                # Save file temporarily
                file_path = os.path.join(self.config.UPLOAD_FOLDER, file.filename)
                file.save(file_path)
                
                # Process document
                result = self.document_service.process_document(
                    file_path=file_path,
                    filename=file.filename,
                    conversation_id=conversation_id
                )
                
                # Clean up temporary file
                if os.path.exists(file_path):
                    os.remove(file_path)
                
                return jsonify(result), 200
            except Exception as e:
                return jsonify({"error": str(e)}), 500
        
        # Query endpoint
        @self.app.route("/ask", methods=["POST"])
        def ask_question():
            """Process a question and return an answer."""
            try:
                data = request.json
                question = data.get("question")
                conversation_id = data.get("conversation_id")
                max_results = data.get("max_results", 200)
                
                if not question:
                    return jsonify({"error": "No question provided"}), 400
                
                # Process query
                answer, similar_docs = self.query_service.process_query(
                    question=question,
                    conversation_id=conversation_id,
                    max_results=max_results
                )
                
                return jsonify({
                    "answer": answer,
                    "similar_docs": similar_docs,
                    "conversation_id": conversation_id
                }), 200
            except Exception as e:
                return jsonify({"error": str(e)}), 500
        
        # Conversation endpoints
        @self.app.route("/conversations", methods=["GET"])
        def get_all_conversations():
            """Get all conversations."""
            try:
                conversations = self.conversation_service.get_all_conversations()
                return jsonify({"conversations": conversations}), 200
            except Exception as e:
                return jsonify({"error": str(e)}), 500
        
        @self.app.route("/conversations", methods=["POST"])
        def create_new_conversation():
            """Create a new conversation."""
            try:
                data = request.json or {}
                title = data.get("title", "New Conversation")
                initial_message = data.get("initial_message", "Hello! How can I help you with your code?")
                
                conversation = self.conversation_service.create_conversation(title, initial_message)
                
                return jsonify(conversation), 201
            except Exception as e:
                return jsonify({"error": str(e)}), 500
        
        @self.app.route("/conversations/<conversation_id>", methods=["GET"])
        def get_single_conversation(conversation_id):
            """Get a specific conversation by ID."""
            try:
                conversation = self.conversation_service.get_conversation(conversation_id)
                
                if not conversation:
                    return jsonify({"error": "Conversation not found"}), 404
                
                return jsonify(conversation), 200
            except Exception as e:
                return jsonify({"error": str(e)}), 500
        
        @self.app.route("/conversations/<conversation_id>", methods=["PUT"])
        def update_conversation(conversation_id):
            """Update a conversation's title."""
            try:
                data = request.json
                if not data:
                    return jsonify({"error": "No data provided"}), 400
                
                title = data.get("title")
                if not title:
                    return jsonify({"error": "Title is required"}), 400
                
                updated = self.conversation_service.update_conversation_title(conversation_id, title)
                
                if not updated:
                    return jsonify({"error": "Conversation not found"}), 404
                
                return jsonify(updated), 200
            except Exception as e:
                return jsonify({"error": str(e)}), 500
        
        @self.app.route("/conversations/<conversation_id>", methods=["DELETE"])
        def delete_single_conversation(conversation_id):
            """Delete a conversation by ID."""
            try:
                success = self.conversation_service.delete_conversation(conversation_id)
                
                if not success:
                    return jsonify({"error": "Conversation not found"}), 404
                
                return jsonify({"message": "Conversation deleted successfully"}), 200
            except Exception as e:
                return jsonify({"error": str(e)}), 500
        
        @self.app.route("/conversations/<conversation_id>/messages", methods=["POST"])
        def add_conversation_message(conversation_id):
            """Add a message to an existing conversation."""
            try:
                data = request.json
                role = data.get("role")
                content = data.get("content")
                
                if not role or not content:
                    return jsonify({"error": "Both 'role' and 'content' fields are required"}), 400
                
                # Add user message
                if role == "user":
                    user_message = self.conversation_service.add_user_message(conversation_id, content)
                    
                    if not user_message:
                        return jsonify({"error": "Conversation not found"}), 404
                    
                    # Generate assistant response
                    answer, _ = self.query_service.process_query(content, conversation_id)
                    
                    # Get the assistant message from the conversation history
                    conversation = self.conversation_service.get_conversation(conversation_id)
                    if conversation and "messages" in conversation:
                        assistant_message = conversation["messages"][-1]
                    else:
                        assistant_message = {"role": "assistant", "content": answer}
                    
                    return jsonify({
                        "user_message": user_message,
                        "assistant_message": assistant_message
                    }), 200
                elif role == "assistant":
                    message = self.conversation_service.add_assistant_message(conversation_id, content)
                elif role == "system":
                    message = self.conversation_service.add_system_message(conversation_id, content)
                else:
                    return jsonify({"error": f"Invalid role: {role}"}), 400
                
                if not message:
                    return jsonify({"error": "Conversation not found"}), 404
                
                return jsonify({"message": message}), 200
            except Exception as e:
                return jsonify({"error": str(e)}), 500
        
        @self.app.route("/conversations/<conversation_id>/documents", methods=["GET"])
        def get_conversation_documents(conversation_id):
            """Get all documents associated with a conversation."""
            try:
                documents = self.conversation_service.get_conversation_documents(conversation_id)
                return jsonify({"documents": documents}), 200
            except Exception as e:
                return jsonify({"error": str(e)}), 500
        
        # Debug endpoint
        @self.app.route("/debug/collection", methods=["GET"])
        def debug_collection():
            """View indexed documents (for debugging)."""
            try:
                # Use a simple question to retrieve documents
                answer, documents = self.query_service.process_query(
                    "Show me all documents", 
                    conversation_id=None,
                    max_results=200
                )
                
                return jsonify({"documents": documents})
            except Exception as e:
                return jsonify({"error": str(e)}), 500
    
    def run(self, host='0.0.0.0', port=5000, debug=False):
        """Run the Flask application."""
        self.app.run(host=host, port=port, debug=debug)
    
    def get_app(self):
        """Get the Flask application instance."""
        return self.app