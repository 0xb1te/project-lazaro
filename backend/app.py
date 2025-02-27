from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import uuid

from .utils.file_processor import process_file, process_zip_file
from langchain_ollama import OllamaLLM
from sentence_transformers import SentenceTransformer

from .config import LLM_MODEL, OLLAMA_BASE_URL
from .utils.qdrant_handler import (
    init_collection, 
    insert_documents, 
    search_similar_documents, 
    clear_collection
)
from .conversation_storage import ConversationStorage

# Initialize Flask app
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# Configuration
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Initialize SentenceTransformer model
model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

# Initialize Qdrant collections at startup
try:
    init_collection()
    print("Qdrant collection initialized successfully")
except Exception as e:
    print(f"Warning: Failed to initialize Qdrant collection: {str(e)}")

# Initialize conversation storage
conversation_storage = ConversationStorage("./storage")

@app.route("/")
def health_check():
    return jsonify({"status": "healthy"}), 200

@app.route("/upload", methods=["POST"])
def upload_file():
    try:
        if "file" not in request.files:
            return jsonify({"error": "No file uploaded"}), 400

        file = request.files["file"]
        if file.filename == "":
            return jsonify({"error": "No file selected"}), 400
            
        # Get conversation ID from request (optional)
        conversation_id = request.form.get("conversation_id")
        
        # If no conversation ID provided, create a new conversation
        if not conversation_id:
            conversation = conversation_storage.create_conversation(
                title=f"Project: {file.filename}",
                initial_message=f"I've indexed your project '{file.filename}'. What would you like to know about it?"
            )
            conversation_id = conversation["id"]
        else:
            # Verify conversation exists
            conversation = conversation_storage.get_conversation(conversation_id)
            if not conversation:
                return jsonify({"error": "Conversation not found"}), 404

        # Save the file temporarily
        file_path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(file_path)

        # Initialize/reset the Qdrant collection
        client = init_collection()
        clear_collection()

        # Process the file based on type
        if file.filename.endswith(".zip"):
            texts = process_zip_file(file_path)
        else:
            texts = process_file(file_path)

        # Generate embeddings
        embeddings = [model.encode(text.page_content).tolist() for text in texts]
        
        # Insert into Qdrant
        insert_documents(texts, embeddings)
        
        # Add document to conversation
        document_info = {
            "id": str(uuid.uuid4()),
            "filename": file.filename,
            "type": "zip" if file.filename.endswith(".zip") else "file"
        }
        conversation_storage.add_document_to_conversation(conversation_id, document_info)
        
        # Clean up temporary file
        os.remove(file_path)

        return jsonify({
            "message": "File indexed successfully. You can now ask questions about it.",
            "conversation_id": conversation_id
        }), 200

    except Exception as e:
        print(f"Error in upload_file: {str(e)}")
        return jsonify({"error": str(e)}), 500

def get_answer_from_context(question, context):
    """Helper function to get an answer to a question using context."""
    # Initialize LLM
    llm = OllamaLLM(
        model=LLM_MODEL,
        base_url=OLLAMA_BASE_URL,
        num_ctx=4096,
        temperature=0.8,
        request_timeout=120.0,
    )
    
    # Create prompt
    prompt = f"""
        You are a helpful assistant named LAZARO. Answer the following question based only on the context provided below as 
        if you were a senior developer, making me understand the codebase and how it works. Follow these rules strictly:

        1. **Code Formatting**:
        - Every block of code should be placed between `<code></code>` tags.
        - Use proper indentation and syntax highlighting for readability.

        2. **Code Quality**:
        - Follow SOLID principles.
        - Ensure the code is clean, modular, and easy to maintain.

        3. **Code Review**:
        - Review your code to ensure it is functional and free of errors.
        - Do not share non-working or incomplete code.

        4. **Explanation**:
        - Provide a clear and concise explanation of the code, always specify the name of the file you are talking about.
        - Explain how the code works and why it solves the problem.
        - Use bullet points or numbered lists for step-by-step explanations if necessary.

        5. **Context Awareness**:
        - Use only the context provided below to generate the answer.
        - Do not make assumptions or include information outside the context.

        6. **Professional Tone**:
        - Use a professional and friendly tone.
        - Avoid jargon unless it is necessary and clearly explained.

        7. **Answer if you the user calls you LAZARO**:
        - Answer without taking into account the provided codebase.
        - If you are called LAZARO, you are free to use information outside the context.

        8. **Preserve Existing Functionality**:
        - When suggesting code changes, always identify and preserve existing functionality.
        - Clearly mark which parts of the code remain unchanged and which parts are modified.
        - If suggesting new code, explain how it integrates with the existing system without breaking current features.
        - When modifying code, include comments explaining the rationale for each change.

        9. **Implementation Guidelines**:
        - Present code modifications as targeted changes rather than complete rewrites when possible.
        - For any suggested changes, explain potential impacts on other parts of the codebase.
        - Provide fallback mechanisms or error handling for any new features.

        Context:
        {context}

        Question:
        {question}

        Answer:
        """

    # Get the answer
    answer = llm.invoke(prompt)
    return answer

def ask_question_internal(question, conversation_id=None):
    """
    Internal function to process a question and get an answer.
    Can be used from both /ask route and conversation routes.
    """
    # Generate embedding for the question
    question_embedding = model.encode(question).tolist()

    # Search for similar documents using Qdrant
    similar_docs = search_similar_documents(question_embedding, limit=5)

    # Extract text content from top documents
    context = " ".join([doc["text"] for doc in similar_docs])
    
    # Get answer
    answer = get_answer_from_context(question, context)
    
    # Add to conversation history if conversation_id is provided
    if conversation_id:
        conversation_storage.add_message(conversation_id, "user", question)
        conversation_storage.add_message(conversation_id, "assistant", answer)
    
    return answer, similar_docs

@app.route("/ask", methods=["POST"])
def ask_question():
    data = request.json
    question = data.get("question")
    conversation_id = data.get("conversation_id")  # Optional

    if not question:
        return jsonify({"error": "No question provided"}), 400

    try:
        answer, similar_docs = ask_question_internal(question, conversation_id)
        
        return jsonify({
            "answer": answer, 
            "similar_docs": similar_docs,
            "conversation_id": conversation_id
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Conversation Routes
@app.route("/conversations", methods=["GET"])
def get_all_conversations():
    """Get all conversations"""
    try:
        conversations = conversation_storage.get_all_conversations()
        return jsonify({"conversations": conversations}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/conversations", methods=["POST"])
def create_new_conversation():
    """Create a new conversation"""
    try:
        data = request.json or {}
        title = data.get("title", "New Conversation")
        initial_message = data.get("initial_message", "Hello! How can I help you with your code?")
        
        conversation = conversation_storage.create_conversation(title, initial_message)
        
        return jsonify(conversation), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/conversations/<conversation_id>", methods=["GET"])
def get_single_conversation(conversation_id):
    """Get a specific conversation by ID"""
    try:
        conversation = conversation_storage.get_conversation(conversation_id)
        
        if not conversation:
            return jsonify({"error": "Conversation not found"}), 404
        
        return jsonify(conversation), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/conversations/<conversation_id>", methods=["PUT"])
def update_conversation(conversation_id):
    """Update a conversation's title"""
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        updates = {}
        if "title" in data:
            updates["title"] = data["title"]
            
        updated = conversation_storage.update_conversation(conversation_id, updates)
        
        if not updated:
            return jsonify({"error": "Conversation not found"}), 404
        
        return jsonify(updated), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/conversations/<conversation_id>", methods=["DELETE"])
def delete_single_conversation(conversation_id):
    """Delete a conversation by ID"""
    try:
        success = conversation_storage.delete_conversation(conversation_id)
        
        if not success:
            return jsonify({"error": "Conversation not found"}), 404
        
        return jsonify({"message": "Conversation deleted successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# In app.py - modify the add_conversation_message function

@app.route("/conversations/<conversation_id>/messages", methods=["POST"])
def add_conversation_message(conversation_id):
    """Add a message to an existing conversation"""
    try:
        data = request.json
        role = data.get("role")
        content = data.get("content")
        
        if not role or not content:
            return jsonify({"error": "Both 'role' and 'content' fields are required"}), 400
        
        # Add user message
        user_message = conversation_storage.add_message(conversation_id, role, content)
        
        if not user_message:
            return jsonify({"error": "Conversation not found"}), 404
        
        # If it's a user message, try to generate assistant response
        if role == "user":
            try:
                # Check if Qdrant collection exists before trying to query it
                client = init_collection()  # This should create the collection if it doesn't exist
                
                # Try to get an answer using the RAG system
                answer, _ = ask_question_internal(content)
            except Exception as e:
                # If there's an error (like missing collection), use a fallback response
                if "doesn't exist" in str(e) or "Collection" in str(e):
                    answer = "I need some documents to help answer your questions. Please upload a file first."
                else:
                    # For other errors, provide a generic response
                    print(f"Error generating response: {str(e)}")
                    answer = "I'm having trouble processing your request. Please try uploading a document first."
            
            # Add assistant message
            assistant_message = conversation_storage.add_message(conversation_id, "assistant", answer)
            
            return jsonify({
                "user_message": user_message,
                "assistant_message": assistant_message
            }), 200
        
        return jsonify({"message": user_message}), 200
    except Exception as e:
        print(f"Error in add_conversation_message: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route("/conversations/<conversation_id>/documents", methods=["GET"])
def get_conversation_documents(conversation_id):
    """Get all documents associated with a conversation"""
    try:
        documents = conversation_storage.get_conversation_documents(conversation_id)
        return jsonify({"documents": documents}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/debug/collection", methods=["GET"])
def debug_collection():
    try:
        question_embedding = model.encode("Show me all documents").tolist()
        documents = search_similar_documents(question_embedding, limit=100)
        return jsonify({"documents": documents})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)