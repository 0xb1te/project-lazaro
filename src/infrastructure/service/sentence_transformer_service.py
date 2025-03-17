# src/infrastructure/service/sentence_transformer_service.py
import logging
import re
import numpy as np
from typing import List, Dict, Any, Optional  # Add Dict and Any to the imports
from sentence_transformers import SentenceTransformer, util

from src.domain.port.service.embedding_service import EmbeddingService

class SentenceTransformerService(EmbeddingService):
    """
    SentenceTransformer-based implementation of the EmbeddingService interface.
    Uses Sentence Transformers to generate text embeddings.
    """
    
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        """
        Initialize the SentenceTransformer service.
        
        Args:
            model_name: Name of the model to use
        """
        self.model_name = model_name
        self.model = SentenceTransformer(model_name)
        self.logger = logging.getLogger(__name__)
        
        # Log model information
        self.logger.info(f"Initialized SentenceTransformer with model: {model_name}")
        self.logger.info(f"Model embedding dimension: {self.get_embedding_dimension()}")
    
    def get_embedding(self, text: str) -> List[float]:
        """
        Generate an embedding vector for a single text.
        
        Args:
            text: The text to generate an embedding for
            
        Returns:
            Embedding vector as a list of floats
        """
        # Normalize text
        normalized_text = self.normalize_text(text)
        
        # Generate embedding
        try:
            embedding = self.model.encode(normalized_text)
            return embedding.tolist()
        except Exception as e:
            self.logger.error(f"Error generating embedding: {str(e)}")
            # Return a zero vector as fallback
            return [0.0] * self.get_embedding_dimension()
    
    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embedding vectors for multiple texts.
        
        Args:
            texts: List of texts to generate embeddings for
            
        Returns:
            List of embedding vectors
        """
        # Normalize texts
        normalized_texts = [self.normalize_text(text) for text in texts]
        
        # Generate embeddings in batch
        try:
            embeddings = self.model.encode(normalized_texts)
            return [embedding.tolist() for embedding in embeddings]
        except Exception as e:
            self.logger.error(f"Error generating batch embeddings: {str(e)}")
            # Return zero vectors as fallback
            dimension = self.get_embedding_dimension()
            return [[0.0] * dimension for _ in range(len(texts))]
    
    def get_embedding_dimension(self) -> int:
        """
        Get the dimension of the embedding vectors.
        
        Returns:
            Embedding dimension
        """
        return self.model.get_sentence_embedding_dimension()
    
    def get_model_name(self) -> str:
        """
        Get the name or identifier of the embedding model.
        
        Returns:
            Model name or identifier
        """
        return self.model_name
    
    def compute_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """
        Compute the cosine similarity between two embedding vectors.
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
            
        Returns:
            Similarity score between 0 and 1
        """
        # Convert to numpy arrays
        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)
        
        # Compute cosine similarity
        try:
            similarity = util.cos_sim(vec1, vec2).item()
            return float(similarity)
        except Exception as e:
            self.logger.error(f"Error computing similarity: {str(e)}")
            return 0.0
    
    def normalize_text(self, text: str) -> str:
        """
        Normalize text before generating embeddings.
        
        Args:
            text: Text to normalize
            
        Returns:
            Normalized text
        """
        # Handle None or empty string
        if not text:
            return ""
        
        # Convert to string if necessary
        if not isinstance(text, str):
            text = str(text)
        
        # Limit text length to avoid excessive token usage
        MAX_LENGTH = 1000000  # Maximum characters
        if len(text) > MAX_LENGTH:
            self.logger.warning(f"Truncating text from {len(text)} to {MAX_LENGTH} characters")
            text = text[:MAX_LENGTH]
        
        # Basic normalization
        # 1. Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        # 2. Remove control characters
        text = ''.join(ch for ch in text if ch.isprintable())
        
        return text
    
    def find_most_similar(self, query_text: str, candidate_texts: List[str], top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Find the most similar texts to a query text.
        
        Args:
            query_text: The query text
            candidate_texts: List of candidate texts to compare against
            top_k: Number of top results to return
            
        Returns:
            List of dictionaries with text and similarity score
        """
        # Generate embeddings
        query_embedding = self.get_embedding(query_text)
        candidate_embeddings = self.get_embeddings(candidate_texts)
        
        # Calculate similarities
        similarities = []
        for i, candidate_embedding in enumerate(candidate_embeddings):
            similarity = self.compute_similarity(query_embedding, candidate_embedding)
            similarities.append((i, similarity))
        
        # Sort by similarity (descending)
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        # Return top-k results
        results = []
        for idx, score in similarities[:top_k]:
            results.append({
                "text": candidate_texts[idx],
                "similarity": score
            })
        
        return results