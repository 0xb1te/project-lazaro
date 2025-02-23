from flask import Flask, request, jsonify
from flask_cors import CORS
from .utils.file_processor import process_file, process_zip_file
from .utils.qdrant_handler import init_collection, insert_documents, search_similar_documents, clear_collection
from langchain_ollama import OllamaLLM
from sentence_transformers import SentenceTransformer
import os
from .config import LLM_MODEL
from .config import OLLAMA_BASE_URL, LLM_MODEL

# Initialize Flask app
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# Configuration
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Initialize SentenceTransformer model
model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

# Initialize Qdrant collection
init_collection()

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

        # Save the file temporarily
        file_path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(file_path)

        # Clear existing documents
        clear_collection()

        # Process files
        if file.filename.endswith(".zip"):
            texts = process_zip_file(file_path)
        else:
            texts = process_file(file_path)

        # Generate embeddings for all texts
        embeddings = [model.encode(text.page_content).tolist() for text in texts]

        # Store documents and embeddings in Qdrant
        insert_documents(texts, embeddings)

        # Clean up
        os.remove(file_path)

        return jsonify({"message": "File indexed successfully"}), 200

    except Exception as e:
        print(f"Error in upload_file: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route("/ask", methods=["POST"])
def ask_question():
    data = request.json
    question = data.get("question")

    if not question:
        return jsonify({"error": "No question provided"}), 400

    # Generate embedding for the question
    question_embedding = model.encode(question).tolist()

    # Search for similar documents in Qdrant
    similar_docs = search_similar_documents(question_embedding, limit=5)

    # Extract the text content from the top documents
    context = " ".join([doc["text"] for doc in similar_docs])

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

        Context:
        {context}

        Question:
        {question}

        Answer:
        """

    # Get the answer
    answer = llm.invoke(prompt)
    
    return jsonify({"answer": answer, "similar_docs": similar_docs}), 200

if __name__ == "__main__":
    app.run(debug=True)