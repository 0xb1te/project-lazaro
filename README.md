# Project Lazaro - RAG System with Hexagonal Architecture

Project Lazaro is a modular Retrieval-Augmented Generation (RAG) system built with a clean hexagonal architecture (ports and adapters pattern). The system allows users to upload documents, ask questions about their content, and maintain conversations in a clean, maintainable, and testable codebase.

## Architecture Overview

The system follows a strict hexagonal architecture with the following layers:

### Domain Layer

- **Core entities**: Conversation, Message, Document, DocumentChunk
- **Ports**: Interfaces for repositories and services that the domain depends on
- **Domain services**: Core business logic and rules

### Application Layer

- **Application services**: Orchestrate use cases by coordinating domain entities
- **DTOs**: Data Transfer Objects for input/output operations
- **Use cases**: Implementations of user interactions with the system

### Infrastructure Layer

- **Repository adapters**: Implementations of repository interfaces (File, Qdrant)
- **Service adapters**: Implementations of service interfaces (Ollama, SentenceTransformer)
- **Dependency injection**: Container to wire up dependencies
- **Configuration**: Environment-based configuration

### Interface Layer

- **API controllers**: Flask-based HTTP interface
- **API DTOs**: Data objects specific to the API interface
- **Error handling**: HTTP-specific error handling and formatting

## Key Features

- **Clean separation of concerns**: Each layer has clear responsibilities
- **Dependency inversion**: Domain doesn't depend on infrastructure
- **Testability**: Components can be tested in isolation
- **Flexibility**: Easy to swap out implementations (e.g., different vector stores)
- **Type safety**: Strong typing throughout the codebase

## Directory Structure

```
/src
  /domain
    /model        # Core entities
    /port         # Interfaces/ports
    /service      # Domain services
  /application
    /dto          # Data transfer objects
    /service      # Application services
  /infrastructure
    /repository   # Repository implementations
    /service      # External service adapters
    /config       # Configuration
    /di           # Dependency injection
    /api          # API controllers
  /interface
    /api          # API controllers
    /dto          # API-specific DTOs
```

## Getting Started

### Prerequisites

- Python 3.8+
- Docker and Docker Compose (optional)
- [Ollama](https://ollama.ai/) for local LLM support

### Installation

1. Clone the repository:

   ```
   git clone https://github.com/yourusername/project-lazaro.git
   cd project-lazaro
   ```

2. Create a virtual environment:

   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   .\venv\Scripts\Activate.ps1 # On Windows
   ```

3. Install dependencies:

   ```
   pip install -r requirements.txt
   ```

4. Set up environment variables (optional):
   Create a `.env` file in the root directory with:
   ```
   QDRANT_HOST=localhost
   QDRANT_PORT=6333
   LLM_MODEL=llama2
   OLLAMA_BASE_URL=http://localhost:11434
   DEBUG_MODE=True
   ```

### Running the Application

#### Development Mode

```
python -m backend
python serve_frontend.py
```

The application will start on http://localhost:5000.

#### Production Mode

```
DEBUG_MODE=False python -m src.run
```

#### Docker

```
docker-compose up -d
```

## API Endpoints

### Health Check

- `GET /`: Get service health and configuration

### Conversations

- `GET /conversations`: Get all conversations
- `POST /conversations`: Create a new conversation
- `GET /conversations/{id}`: Get a conversation by ID
- `PUT /conversations/{id}`: Update a conversation
- `DELETE /conversations/{id}`: Delete a conversation
- `POST /conversations/{id}/messages`: Add a message to a conversation
- `GET /conversations/{id}/documents`: Get documents associated with a conversation

### Documents

- `POST /upload`: Upload and process a document

### Queries

- `POST /ask`: Ask a question about uploaded documents

## Development

### Adding a New Repository Implementation

1. Create a new implementation in `src/infrastructure/repository/`
2. Implement the relevant interface from `src/domain/port/repository/`
3. Update the dependency injection container in `src/infrastructure/di/container.py`

### Adding a New Service Implementation

1. Create a new implementation in `src/infrastructure/service/`
2. Implement the relevant interface from `src/domain/port/service/`
3. Update the dependency injection container in `src/infrastructure/di/container.py`

### Running Tests

```
pytest
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.
