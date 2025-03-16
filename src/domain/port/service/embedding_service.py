# src/domain/port/service/embedding_service.py
from abc import ABC, abstractmethod
from typing import List, Optional

class EmbeddingService(ABC):
    """
    Port (interface) defining operations for generating embeddings.
    This interface allows the domain and application layers to interact with
    embedding generation services without knowing the specific implementation.
    
    Implementations of this interface might use SentenceTransformers, OpenAI embeddings,
    or other embedding models.
    """
    
    @abstractmethod
    def get_embedding(self, text: str) -> List[float]:
        """
        Generate an embedding vector for a single text.
        
        Args:
            text: The text to generate an embedding for
            
        Returns:
            Embedding vector as a list of floats
        """
        pass
    
    @abstractmethod
    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embedding vectors for multiple texts.
        
        Args:
            texts: List of texts to generate embeddings for
            
        Returns:
            List of embedding vectors
        """
        pass
    
    @abstractmethod
    def get_embedding_dimension(self) -> int:
        """
        Get the dimension of the embedding vectors.
        
        Returns:
            Embedding dimension
        """
        pass
    
    @abstractmethod
    def get_model_name(self) -> str:
        """
        Get the name or identifier of the embedding model.
        
        Returns:
            Model name or identifier
        """
        pass
    
    @abstractmethod
    def compute_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """
        Compute the similarity between two embedding vectors.
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
            
        Returns:
            Similarity score between 0 and 1
        """
        pass
    
    @abstractmethod
    def normalize_text(self, text: str) -> str:
        """
        Normalize text before generating embeddings.
        
        Args:
            text: Text to normalize
            
        Returns:
            Normalized text
        """
        pass