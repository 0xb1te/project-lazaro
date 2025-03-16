# src/domain/model/document_chunk.py
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
import uuid

@dataclass
class DocumentChunk:
    """
    Domain entity representing a chunk of a document with its content, metadata, and embedding.
    Document chunks are the units stored in the vector database for retrieval.
    """
    
    content: str
    metadata: Dict[str, Any]
    id: str = None
    embedding: Optional[List[float]] = None
    
    def __post_init__(self):
        """Initialize default values if not provided."""
        # Generate ID if not provided
        if self.id is None:
            self.id = str(uuid.uuid4())
        
        # Initialize empty metadata if None
        if self.metadata is None:
            self.metadata = {}
    
    def add_metadata(self, key: str, value: Any) -> None:
        """
        Add a metadata field to the document chunk.
        
        Args:
            key: Metadata key
            value: Metadata value
        """
        self.metadata[key] = value
    
    def get_metadata(self, key: str, default: Any = None) -> Any:
        """
        Get a metadata field from the document chunk.
        
        Args:
            key: Metadata key
            default: Default value if key doesn't exist
            
        Returns:
            The metadata value or default
        """
        return self.metadata.get(key, default)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary representation for serialization.
        
        Returns:
            Dictionary representation of the document chunk
        """
        result = {
            "id": self.id,
            "content": self.content,
            "metadata": self.metadata
        }
        
        # Only include embedding if it exists
        if self.embedding is not None:
            result["embedding"] = self.embedding
            
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DocumentChunk':
        """
        Create a DocumentChunk instance from a dictionary.
        
        Args:
            data: Dictionary representation of a document chunk
            
        Returns:
            DocumentChunk instance
        """
        return cls(
            id=data.get("id"),
            content=data.get("content", ""),
            metadata=data.get("metadata", {}),
            embedding=data.get("embedding")
        )
    
    @classmethod
    def from_langchain_document(cls, document: Any, embedding: Optional[List[float]] = None) -> 'DocumentChunk':
        """
        Create a DocumentChunk from a LangChain Document.
        
        Args:
            document: LangChain Document instance
            embedding: Optional embedding vector
            
        Returns:
            DocumentChunk instance
        """
        # Extract content and metadata from LangChain Document
        content = getattr(document, "page_content", "")
        metadata = getattr(document, "metadata", {})
        
        return cls(
            content=content,
            metadata=metadata,
            embedding=embedding
        )