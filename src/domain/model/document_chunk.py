# src/domain/model/document_chunk.py
from dataclasses import dataclass, field
from typing import Dict, Any, Optional
import uuid

@dataclass
class DocumentChunk:
    """
    Domain entity representing a chunk of text from a document.
    Each document can be split into multiple chunks for efficient retrieval.
    """
    
    content: str
    metadata: Dict[str, Any]
    document_id: str
    chunk_id: str = None
    embedding: Optional[list] = None
    
    def __post_init__(self):
        """Initialize default values if not provided."""
        # Generate ID if not provided
        if self.chunk_id is None:
            self.chunk_id = str(uuid.uuid4())
        
        # Ensure metadata is a dictionary
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
        return {
            "chunk_id": self.chunk_id,
            "document_id": self.document_id,
            "content": self.content,
            "metadata": self.metadata,
            "embedding": self.embedding
        }
    
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
            chunk_id=data.get("chunk_id"),
            document_id=data.get("document_id"),
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