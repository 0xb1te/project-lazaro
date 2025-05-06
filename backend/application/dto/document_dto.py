from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime

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

@dataclass
class DocumentDTO:
    """Data Transfer Object for a document."""
    
    id: str
    filename: str
    file_type: str
    added_at: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)
    conversation_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "filename": self.filename,
            "file_type": self.file_type,
            "added_at": self.added_at.isoformat(),
            "metadata": self.metadata,
            "conversation_id": self.conversation_id
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DocumentDTO':
        """Create a DocumentDTO from a dictionary."""
        added_at = data.get("added_at")
        if isinstance(added_at, str):
            try:
                added_at = datetime.fromisoformat(added_at)
            except ValueError:
                added_at = datetime.utcnow()
        else:
            added_at = datetime.utcnow()
            
        return cls(
            id=data.get("id", ""),
            filename=data.get("filename", ""),
            file_type=data.get("file_type", "file"),
            added_at=added_at,
            metadata=data.get("metadata", {}),
            conversation_id=data.get("conversation_id")
        )

@dataclass
class DocumentChunkDTO:
    """Data Transfer Object for a document chunk."""
    
    text: str
    similarity: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    id: Optional[str] = None
    document_id: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DocumentChunkDTO':
        """Create a DocumentChunkDTO from a dictionary."""
        return cls(
            id=data.get("id"),
            document_id=data.get("document_id"),
            text=data.get("text", ""),
            similarity=data.get("similarity", 0.0),
            metadata=data.get("metadata", {})
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "document_id": self.document_id,
            "text": self.text,
            "similarity": self.similarity,
            "metadata": self.metadata
        } 