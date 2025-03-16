# src/domain/model/document.py
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional
import uuid

@dataclass
class Document:
    """
    Domain entity representing a document reference in a conversation.
    This is a reference to an uploaded document, not the document content itself.
    The actual content is stored as DocumentChunks in the vector database.
    """
    
    filename: str
    type: str  # 'file', 'zip', etc.
    added_at: datetime
    id: str = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Initialize default values if not provided."""
        # Generate ID if not provided
        if self.id is None:
            self.id = str(uuid.uuid4())
        
        # Ensure datetime objects
        if isinstance(self.added_at, str):
            self.added_at = datetime.fromisoformat(self.added_at)
        
        # Initialize empty metadata if None
        if self.metadata is None:
            self.metadata = {}
    
    def add_metadata(self, key: str, value: Any) -> None:
        """
        Add a metadata field to the document.
        
        Args:
            key: Metadata key
            value: Metadata value
        """
        self.metadata[key] = value
    
    def get_metadata(self, key: str, default: Any = None) -> Any:
        """
        Get a metadata field from the document.
        
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
            Dictionary representation of the document
        """
        return {
            "id": self.id,
            "filename": self.filename,
            "type": self.type,
            "added_at": self.added_at.isoformat(),
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Document':
        """
        Create a Document instance from a dictionary.
        
        Args:
            data: Dictionary representation of a document
            
        Returns:
            Document instance
        """
        return cls(
            id=data.get("id"),
            filename=data.get("filename", "unnamed_document"),
            type=data.get("type", "file"),
            added_at=data.get("added_at", datetime.utcnow().isoformat()),
            metadata=data.get("metadata", {})
        )
    
    @property
    def is_compressed(self) -> bool:
        """
        Check if the document has compression enabled.
        
        Returns:
            True if compression is enabled, False otherwise
        """
        return self.metadata.get("compression_enabled", False)
    
    @property
    def chunk_count(self) -> int:
        """
        Get the number of chunks in the document.
        
        Returns:
            Number of chunks or 0 if unknown
        """
        return self.metadata.get("chunk_count", 0)
    
    @property
    def file_size(self) -> int:
        """
        Get the file size in bytes.
        
        Returns:
            File size in bytes or 0 if unknown
        """
        return self.metadata.get("file_size", 0)
    
    @property
    def extension(self) -> str:
        """
        Get the file extension.
        
        Returns:
            File extension (without the dot) or empty string if no extension
        """
        if "." in self.filename:
            return self.filename.split(".")[-1].lower()
        return ""
    
    @property
    def is_zip(self) -> bool:
        """
        Check if the document is a ZIP file.
        
        Returns:
            True if the document is a ZIP file, False otherwise
        """
        return self.type == "zip" or self.extension == "zip"