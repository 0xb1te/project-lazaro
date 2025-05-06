from typing import Dict, Any

from src.domain.port.repository.conversation_repository import ConversationRepository
from src.domain.port.repository.vector_repository import VectorRepository
from src.domain.port.service.embedding_service import EmbeddingService
from src.domain.port.service.llm_service import LlmService
from src.domain.port.service.document_processor_service import DocumentProcessorService

from src.infrastructure.repository.file_conversation_repository import FileConversationRepository
from src.infrastructure.repository.qdrant_vector_repository import QdrantVectorRepository
from src.infrastructure.service.sentence_transformer_service import SentenceTransformerService
from src.infrastructure.service.ollama_service import OllamaService
from src.infrastructure.service.document_processor import DocumentProcessor

from src.application.service.conversation_service import ConversationService
from src.application.service.document_service import DocumentService
from src.application.service.query_service import QueryService

from src.infrastructure.config import Config

class Container:
    """
    Dependency Injection Container for the application.
    This class is responsible for creating and providing all application components
    and managing their dependencies.
    """
    
    def __init__(self, config: Config):
        """
        Initialize the container with configuration.
        
        Args:
            config: Application configuration
        """
        self.config = config
        self._instances: Dict[str, Any] = {}
    
    def get_conversation_repository(self) -> ConversationRepository:
        """Get the conversation repository instance."""
        if "conversation_repository" not in self._instances:
            self._instances["conversation_repository"] = FileConversationRepository(
                storage_dir=self.config.STORAGE_DIR
            )
        return self._instances["conversation_repository"]
    
    def get_vector_repository(self) -> VectorRepository:
        """Get the vector repository instance."""
        if "vector_repository" not in self._instances:
            self._instances["vector_repository"] = QdrantVectorRepository(
                host=self.config.QDRANT_HOST,
                port=self.config.QDRANT_PORT,
                collection_name=self.config.COLLECTION_NAME,
                embedding_dimension=self.config.EMBEDDING_DIMENSION
            )
        return self._instances["vector_repository"]
    
    def get_embedding_service(self) -> EmbeddingService:
        """Get the embedding service instance."""
        if "embedding_service" not in self._instances:
            self._instances["embedding_service"] = SentenceTransformerService(
                model_name=self.config.EMBEDDING_MODEL
            )
        return self._instances["embedding_service"]
    
    def get_llm_service(self) -> LlmService:
        """Get the language model service instance."""
        if "llm_service" not in self._instances:
            self._instances["llm_service"] = OllamaService(
                base_url=self.config.OLLAMA_BASE_URL,
                model_name=self.config.LLM_MODEL,
                num_ctx=self.config.MAX_CONTEXT_LENGTH
            )
        return self._instances["llm_service"]
    
    def get_document_processor(self) -> DocumentProcessorService:
        """Get the document processor service instance."""
        if "document_processor" not in self._instances:
            self._instances["document_processor"] = DocumentProcessor(
                upload_folder=self.config.UPLOAD_FOLDER
            )
        return self._instances["document_processor"]
    
    def get_conversation_service(self) -> ConversationService:
        """Get the conversation service instance."""
        if "conversation_service" not in self._instances:
            self._instances["conversation_service"] = ConversationService(
                conversation_repository=self.get_conversation_repository()
            )
        return self._instances["conversation_service"]
    
    def get_document_service(self) -> DocumentService:
        """Get the document service instance."""
        if "document_service" not in self._instances:
            self._instances["document_service"] = DocumentService(
                vector_repository=self.get_vector_repository(),
                embedding_service=self.get_embedding_service(),
                document_processor=self.get_document_processor(),
                conversation_service=self.get_conversation_service()
            )
        return self._instances["document_service"]
    
    def get_query_service(self) -> QueryService:
        """Get the query service instance."""
        if "query_service" not in self._instances:
            self._instances["query_service"] = QueryService(
                vector_repository=self.get_vector_repository(),
                embedding_service=self.get_embedding_service(),
                llm_service=self.get_llm_service(),
                conversation_service=self.get_conversation_service()
            )
        return self._instances["query_service"]
