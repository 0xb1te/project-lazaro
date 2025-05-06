# src/domain/port/service/embedding_service.py
from abc import ABC, abstractmethod
from typing import List, Union

class EmbeddingService(ABC):
    """
    Port (interface) for embedding generation services.
    This interface defines operations for converting text to vector embeddings.
    
    Implementations might use different embedding models or services.
    """
    
    @abstractmethod
    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate an embedding vector for a single text input.
        
        Args:
            text: The text to generate an embedding for
            
        Returns:
            A list of floating-point values representing the embedding vector
        """
        pass
    
    @abstractmethod
    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embedding vectors for a batch of text inputs.
        
        Args:
            texts: The list of texts to generate embeddings for
            
        Returns:
            A list of embedding vectors
        """
        pass
    
    @abstractmethod
    def get_embedding_dimension(self) -> int:
        """
        Get the dimension of the embedding vectors.
        
        Returns:
            The dimension (number of elements) of the embedding vectors
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