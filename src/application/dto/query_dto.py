# src/application/dto/query_dto.py
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime

@dataclass
class QueryRequestDTO:
    """Data Transfer Object for a query request."""
    
    question: str
    conversation_id: Optional[str] = None
    max_results: int = 200
    include_metadata: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "question": self.question,
            "conversation_id": self.conversation_id,
            "max_results": self.max_results,
            "include_metadata": self.include_metadata
        }

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
class QueryResponseDTO:
    """Data Transfer Object for a query response."""
    
    answer: str
    similar_documents: List[DocumentChunkDTO] = field(default_factory=list)
    conversation_id: Optional[str] = None
    processing_time_ms: Optional[float] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'QueryResponseDTO':
        """Create a QueryResponseDTO from a dictionary."""
        similar_docs = [
            DocumentChunkDTO.from_dict(doc) 
            for doc in data.get("similar_documents", [])
        ]
        
        return cls(
            answer=data.get("answer", ""),
            similar_documents=similar_docs,
            conversation_id=data.get("conversation_id"),
            processing_time_ms=data.get("processing_time_ms")
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        result = {
            "answer": self.answer,
            "similar_documents": [doc.to_dict() for doc in self.similar_documents],
            "conversation_id": self.conversation_id
        }
        
        if self.processing_time_ms is not None:
            result["processing_time_ms"] = self.processing_time_ms
        
        return result

@dataclass
class DocumentUploadRequestDTO:
    """Data Transfer Object for a document upload request."""
    
    file_path: str
    filename: str
    conversation_id: Optional[str] = None
    clear_collection: bool = True
    compression_enabled: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "file_path": self.file_path,
            "filename": self.filename,
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