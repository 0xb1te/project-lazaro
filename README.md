# Code Query Application

This application allows users to drag and drop project files, index them in a Qdrant database, and ask questions about the code using Ollama's local LLM. Built with Flask, Qdrant, and Ollama.

## Features

- 📁 Drag and drop file upload support
- 🔍 Advanced code search using vector embeddings
- 💡 Intelligent code analysis with local LLM
- 🚀 Fast response times using Qdrant vector database
- 🐳 Docker support for easy deployment

## Prerequisites

- Python 3.8+
- Docker and Docker Compose
- Ollama installed locally
- Necessary LLM model downloaded (e.g., `deepseek-coder:6.7b`)

## Quick Start (Recommended)

1. Clone the repository:

   ```bash
   git clone <your-repo-url>
   cd code-query-app
   ```

2. Set up environment variables:

   ```bash
   cp .env.example .env
   ```

3. Configure your `.env` file:

   ```env
   QDRANT_HOST=localhost
   QDRANT_PORT=6333
   COLLECTION_NAME=code_chunks
   LLM_MODEL=deepseek-coder:6.7b
   ```

4. Run with Docker:

   ```bash
   docker-compose up --build
   ```

5. Access the application:
   - Frontend: http://localhost
   - Qdrant UI: http://localhost:6334
   - API: http://localhost:5000

## Manual Setup (Without Docker)

1. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

2. Start Ollama and download the model:

   ```bash
   ollama run deepseek-coder:6.7b
   ```

3. Run the application:
   ```bash
   python run.py
   ```

## Project Structure

```
code-query-app/
├── backend/
│   ├── __init__.py
│   ├── app.py
│   ├── config.py
│   └── utils/
├── frontend/
│   ├── index.html
│   ├── styles.css
│   └── script.js
├── nginx/
│   └── default.conf
├── Dockerfile.backend
├── Dockerfile.frontend
├── docker-compose.yml
├── requirements.txt
├── setup.py
└── run.py
```

## API Endpoints

- `POST /upload`: Upload and index files
- `POST /ask`: Query the codebase
- `GET /debug/collection`: View indexed documents

## Development

To run in development mode:

1. Start the application with Docker:

   ```bash
   docker-compose up --build
   ```

2. For live development:
   ```bash
   # In a new terminal, watch for changes
   docker-compose logs -f
   ```

## Acknowledgments

This project is inspired by [Eugene Tan's article on Ollama](https://medium.com/@eugenetan_91090/what-is-ollama-dfdaa40cfbca).

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
