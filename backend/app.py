from flask import Flask, request, jsonify
from flask_cors import CORS
from backend.utils.file_processor import process_file, process_zip_file
from backend.utils.db_handler import get_db_collection
from sklearn.metrics.pairwise import cosine_similarity
from langchain_ollama import OllamaLLM  # Use OllamaLLM if it's a valid class
from sentence_transformers import SentenceTransformer
import os
from dotenv import load_dotenv

app = Flask(__name__)
CORS(app)  # Allow all origins

load_dotenv()

# Configuration
LLM_MODEL = os.getenv("LLM_MODEL")
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Initialize SentenceTransformer model
model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

@app.route("/upload", methods=["POST"])
def upload_file():
    try:
        if "file" not in request.files:
            return jsonify({"error": "No file uploaded"}), 400

        file = request.files["file"]
        if file.filename == "":
            return jsonify({"error": "No file selected"}), 400

        # Save the file temporarily
        file_path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(file_path)

        # Get database collection
        collection = get_db_collection()
        
        # Delete all existing documents in the collection
        collection.delete_many({})

        # Check if the file is a zip file
        if file.filename.endswith(".zip"):
            # Process the zip file
            texts = process_zip_file(file_path)
        else:
            # Process the file
            texts = process_file(file_path)

        # Generate embeddings and store in MongoDB
        for text in texts:
            # Generate embedding using SentenceTransformer
            embedding = model.encode(text.page_content).tolist()

            # Store the embedding along with the text
            collection.insert_one({
                "text": text.page_content,
                "embedding": embedding,
                "metadata": text.metadata  # Include metadata in the database
            })

        # Clean up the temporary file
        os.remove(file_path)

        return jsonify({"message": "File indexed successfully"}), 200

    except Exception as e:
        # Log the error and return a JSON response
        print(f"Error in upload_file: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route("/ask", methods=["POST"])
def ask_question():
    data = request.json
    question = data.get("question")

    if not question:
        return jsonify({"error": "No question provided"}), 400

    # Retrieve all documents from the collection
    collection = get_db_collection()
    all_docs = list(collection.find({}))

    # Generate embedding for the question
    question_embedding = model.encode(question).tolist()

    # Calculate similarity between the question embedding and each document's embedding
    similar_docs = []
    for doc in all_docs:
        if "embedding" in doc:  # Ensure the document has an embedding
            doc_embedding = doc["embedding"]
            similarity = cosine_similarity([question_embedding], [doc_embedding])[0][0]
            similar_docs.append({
                "text": doc["text"],
                "similarity": similarity,
                "_id": str(doc["_id"])  # Convert ObjectId to string for JSON serialization
            })

    # Sort documents by similarity (descending order)
    similar_docs.sort(key=lambda x: x["similarity"], reverse=True)

    # Limit to the top 5 most similar documents
    top_docs = similar_docs[:5]

    # Extract the text content from the top documents
    context = " ".join([doc["text"] for doc in top_docs])

    # Use OllamaLLM to generate an answer based on the retrieved documents
    llm = OllamaLLM(
        model=LLM_MODEL, 
        base_url="http://localhost:11434",  # Specify Ollama server URL
        num_ctx=4096,  # Context window size
        temperature=0.8,
        # Additional parameters if needed
        request_timeout=120.0,  # Increase timeout for longer responses
    )
    
    # Create a prompt that includes the context and the question
    prompt = f"""
        You are a helpful assistant named LAZARO. Answer the following question based only on the context provided below as 
        if you were a senior developer, making me understand the codebase and how it works. Follow these rules strictly:

        1. **Code Formatting**:
        - Every block of code should be placed between `<code></code>` tags.
        - Use proper indentation and syntax highlighting for readability.

        2. **Code Quality**:
        - Follow SOLID principles (Single Responsibility, Open/Closed, Liskov Substitution, Interface Segregation, Dependency Inversion).
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

        Context:
        {context}

        Question:
        {question}

        Answer:
        """

    # Get the answer
    answer = llm.invoke(prompt)
    
    return jsonify({"answer": answer, "similar_docs": top_docs}), 200

@app.route("/debug/collection", methods=["GET"])
def debug_collection():
    # Retrieve the collection
    collection = get_db_collection()

    # Fetch all documents from the collection
    documents = list(collection.find({}))

    # Convert ObjectId to string for JSON serialization
    for doc in documents:
        doc["_id"] = str(doc["_id"])

    return jsonify({"documents": documents})

if __name__ == "__main__":
    app.run(debug=True)