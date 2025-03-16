from typing import Dict, Any, Optional

from src.infrastructure.config import Config
from src.domain.port.repository.conversation_repository import ConversationRepository
from src.domain.port.repository.vector_repository import VectorRepository
from src.domain.port.service.embedding_service import EmbeddingService
from src.domain.port.service.llm_service import LLMService
from src.application.service.conversation_service import ConversationService
from src.application.service.document_service import DocumentService
from src.application.service.query_service import QueryService
from src.infrastructure.repository.file_conversation_repository import FileConversationRepository
from src.infrastructure.repository.qdrant_vector_repository import QdrantVectorRepository
from src.infrastructure.service.sentence_transformer_service import SentenceTransformerService
from src.infrastructure.service.ollama_service import OllamaService

class Container:
    """
    Dependency injection container.
    This class manages the creation and lifecycle of application components.
    """
    
    def __init__(self, config: Config):
        """
        Initialize the container with configuration.
        
        Args:
            config: Application configuration
        """
        self.config = config
        self._instances: Dict[str, Any] = {}
    
    def conversation_repository(self) -> ConversationRepository:
        """Get or create the conversation repository."""
        if 'conversation_repository' not in self._instances:
            self._instances['conversation_repository'] = FileConversationRepository(
                storage_dir=self.config.STORAGE_DIR
            )
        return self._instances['conversation_repository']
    
    def vector_repository(self) -> VectorRepository:
        """Get or create the vector repository."""
        if 'vector_repository' not in self._instances:
            repo = QdrantVectorRepository(
                host=self.config.QDRANT_HOST,
                port=self.config.QDRANT_PORT
            )
            # Initialize the collection
            repo.initialize_collection(
                collection_name=self.config.COLLECTION_NAME,
                dimension=self.config.EMBEDDING_DIMENSION
            )
            self._instances['vector_repository'] = repo
        return self._instances['vector_repository']
    
    def embedding_service(self) -> EmbeddingService:
        """Get or create the embedding service."""
        if 'embedding_service' not in self._instances:
            self._instances['embedding_service'] = SentenceTransformerService(
                model_name=self.config.EMBEDDING_MODEL
            )
        return self._instances['embedding_service']
    
    def llm_service(self) -> LLMService:
        """Get or create the LLM service."""
        if 'llm_service' not in self._instances:
            self._instances['llm_service'] = OllamaService(
                model_name=self.config.LLM_MODEL,
                base_url=self.config.OLLAMA_BASE_URL,
                temperature=self.config.TEMPERATURE
            )
        return self._instances['llm_service']
    
    def conversation_service(self) -> ConversationService:
        """Get or create the conversation service."""
        if 'conversation_service' not in self._instances:
            self._instances['conversation_service'] = ConversationService(
                conversation_repository=self.conversation_repository()
            )
        return self._instances['conversation_service']
    
    def document_service(self) -> DocumentService:
        """Get or create the document service."""
        if 'document_service' not in self._instances:
            self._instances['document_service'] = DocumentService(
                vector_repository=self.vector_repository(),
                embedding_service=self.embedding_service(),
                conversation_service=self.conversation_service(),
                collection_name=self.config.COLLECTION_NAME,
                upload_folder=self.config.UPLOAD_FOLDER
            )
        return self._instances['document_service']
    
    def query_service(self) -> QueryService:
        """Get or create the query service."""
        if 'query_service' not in self._instances:
            self._instances['query_service'] = QueryService(
                vector_repository=self.vector_repository(),
                embedding_service=self.embedding_service(),
                llm_service=self.llm_service(),
                conversation_service=self.conversation_service(),
                collection_name=self.config.COLLECTION_NAME
            )
        return self._instances['query_service']
