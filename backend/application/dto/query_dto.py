# src/application/dto/query_dto.py
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
import os

@dataclass
class QueryRequestDTO:
    """
    Data Transfer Object for a query request from the client.
    """
    query: str
    conversation_id: Optional[str] = None
    max_results: int = 150
    temperature: float = 0.7
    include_context: bool = True

@dataclass
class RetrievedChunkDTO:
    """
    Data Transfer Object for document chunks retrieved from the vector store.
    """
    chunk_id: str
    document_id: str
    content: str
    metadata: Dict[str, Any]
    score: float

@dataclass
class QueryResponseDTO:
    """Data Transfer Object for a query response."""
    query: str
    response: str
    conversation_id: Optional[str] = None
    context: Optional[str] = None
    chunks: Optional[List[Dict[str, Any]]] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "query": self.query,
            "response": self.response,
            "conversation_id": self.conversation_id,
            "context": self.context if self.context else None,
            "chunks": self.chunks if self.chunks else None,
            "timestamp": self.timestamp.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'QueryResponseDTO':
        """Create from dictionary representation."""
        retrieved_chunks = []
        for chunk_data in data.get("retrieved_chunks", []):
            chunk = RetrievedChunkDTO(
                chunk_id=chunk_data.get("chunk_id", ""),
                document_id=chunk_data.get("document_id", ""),
                content=chunk_data.get("content", ""),
                metadata=chunk_data.get("metadata", {}),
                score=chunk_data.get("score", 0.0)
            )
            retrieved_chunks.append(chunk)
        
        timestamp = data.get("timestamp")
        if timestamp and isinstance(timestamp, str):
            try:
                timestamp = datetime.fromisoformat(timestamp)
            except ValueError:
                timestamp = datetime.utcnow()
        else:
            timestamp = datetime.utcnow()
        
        return cls(
            response=data.get("response", ""),
            query=data.get("query", ""),
            conversation_id=data.get("conversation_id"),
            context=data.get("context"),
            chunks=[chunk.to_dict() for chunk in retrieved_chunks],
            timestamp=timestamp
        )

@dataclass
class DocumentChunkDTO:
    """Data Transfer Object for a document chunk in search results."""
    
    text: str
    similarity: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    id: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DocumentChunkDTO':
        """Create a DocumentChunkDTO from a dictionary."""
        return cls(
            id=data.get("id"),
            text=data.get("text", ""),
            similarity=data.get("similarity", 0.0),
            metadata=data.get("metadata", {})
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "text": self.text,
            "similarity": self.similarity,
            "metadata": self.metadata
        }

@dataclass
class DocumentUploadRequestDTO:
    """Data Transfer Object for a document upload request."""
    
    filename: str
    file_path: str  # Path to the uploaded file
    conversation_id: Optional[str] = None
    clear_collection: bool = True
    compression_enabled: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "filename": self.filename,
            "file_path": self.file_path,
            "conversation_id": self.conversation_id,
            "clear_collection": self.clear_collection,
            "compression_enabled": self.compression_enabled
        }

@dataclass
class DocumentUploadResponseDTO:
    """Data Transfer Object for a document upload response."""
    
    message: str
    conversation_id: str
    document_id: str
    compression_enabled: bool
    chunks_processed: int
    file_type: str
    processing_time_ms: Optional[float] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DocumentUploadResponseDTO':
        """Create a DocumentUploadResponseDTO from a dictionary."""
        return cls(
            message=data.get("message", ""),
            conversation_id=data.get("conversation_id", ""),
            document_id=data.get("document_id", ""),
            compression_enabled=data.get("compression_enabled", False),
            chunks_processed=data.get("chunks_processed", 0),
            file_type=data.get("file_type", "file"),
            processing_time_ms=data.get("processing_time_ms")
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        result = {
            "message": self.message,
            "conversation_id": self.conversation_id,
            "document_id": self.document_id,
            "compression_enabled": self.compression_enabled,
            "chunks_processed": self.chunks_processed,
            "file_type": self.file_type
        }
        
        if self.processing_time_ms is not None:
            result["processing_time_ms"] = self.processing_time_ms
        
        return result
