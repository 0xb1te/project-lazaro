# src/domain/port/repository/vector_repository.py
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from backend.domain.model.document_chunk import DocumentChunk

class VectorRepository(ABC):
    """
    Port (interface) defining operations for vector storage and retrieval.
    This interface allows the domain and application layers to interact with
    vector databases without knowing the implementation details.
    
    Implementations of this interface might use Qdrant, FAISS, Pinecone,
    or other vector databases.
    """
    
    @abstractmethod
    def initialize_collection(self, collection_name: str, dimension: int = 384) -> None:
        """
        Initialize a vector collection.
        
        Args:
            collection_name: Name of the collection
            dimension: Dimension of the vectors
        """
        pass
    
    @abstractmethod
    def add_documents(self, collection_name: str, document_chunks: List[DocumentChunk]) -> List[str]:
        """
        Add document chunks with embeddings to the vector database.
        
        Args:
            collection_name: Name of the collection
            document_chunks: List of document chunks with embeddings
            
        Returns:
            List of IDs of the added documents
        """
        pass
    
    @abstractmethod
    def search_similar(self, 
                      collection_name: str, 
                      query_vector: List[float], 
                      limit: int = 200,
                      filter_criteria: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Search for document chunks similar to a query vector.
        
        Args:
            collection_name: Name of the collection
            query_vector: Vector to search for
            limit: Maximum number of results
            filter_criteria: Optional filter criteria
            
        Returns:
            List of document chunks with similarity scores
        """
        pass
    
    @abstractmethod
    def clear_collection(self, collection_name: str) -> None:
        """
        Clear all documents from a collection.
        
        Args:
            collection_name: Name of the collection
        """
        pass
    
    @abstractmethod
    def delete_collection(self, collection_name: str) -> None:
        """
        Delete a collection.
        
        Args:
            collection_name: Name of the collection
        """
        pass
    
    @abstractmethod
    def get_collection_info(self, collection_name: str) -> Dict[str, Any]:
        """
        Get information about a collection.
        
        Args:
            collection_name: Name of the collection
            
        Returns:
            Dictionary with collection information
        """
        pass
    
    @abstractmethod
    def get_document_by_id(self, collection_name: str, document_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a document by ID.
        
        Args:
            collection_name: Name of the collection
            document_id: ID of the document
            
        Returns:
            Document data if found, None otherwise
        """
        pass
    
    @abstractmethod
    def delete_documents(self, collection_name: str, document_ids: List[str]) -> int:
        """
        Delete documents by ID.
        
        Args:
            collection_name: Name of the collection
            document_ids: List of document IDs to delete
            
        Returns:
            Number of documents deleted
        """
        pass
    
    @abstractmethod
    def search_by_metadata(self, 
                          collection_name: str, 
                          metadata_filter: Dict[str, Any],
                          limit: int = 200) -> List[Dict[str, Any]]:
        """
        Search for documents by metadata.
        
        Args:
            collection_name: Name of the collection
            metadata_filter: Filter criteria for metadata
            limit: Maximum number of results
            
        Returns:
            List of documents matching the metadata filter
        """
        pass

    @abstractmethod
    def create_conversation_collection(self, conversation_id: str) -> str:
        """
        Create a new collection for a conversation.
        
        Args:
            conversation_id: ID of the conversation
            
        Returns:
            Name of the created collection
        """
        pass

    @abstractmethod
    def list_conversation_collections(self) -> List[str]:
        """
        List all collections associated with conversations.
        
        Returns:
            List of collection names
        """
        pass

    @abstractmethod
    def delete_conversation_collection(self, conversation_id: str) -> None:
        """
        Delete a collection associated with a conversation.
        
        Args:
            conversation_id: ID of the conversation
        """
        pass
