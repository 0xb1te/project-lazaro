# src/application/dto/conversation_dto.py
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime

@dataclass
class MessageDTO:
    """Data Transfer Object for a message in a conversation."""
    
    role: str  # 'user', 'assistant', 'system'
    content: str
    timestamp: str
    id: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MessageDTO':
        """Create a MessageDTO from a dictionary."""
        return cls(
            id=data.get("id"),
            role=data.get("role", ""),
            content=data.get("content", ""),
            timestamp=data.get("timestamp", datetime.utcnow().isoformat())
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp
        }
    
    def __iter__(self):
        """Make ConversationDTO iterable to prevent runtime errors."""
        # Return an empty iterator by default
        return iter([])

@dataclass
class DocumentDTO:
    """Data Transfer Object for a document reference in a conversation."""
    
    filename: str
    type: str  # 'file', 'zip', etc.
    added_at: str
    id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DocumentDTO':
        """Create a DocumentDTO from a dictionary."""
        return cls(
            id=data.get("id"),
            filename=data.get("filename", ""),
            type=data.get("type", "file"),
            added_at=data.get("added_at", datetime.utcnow().isoformat()),
            metadata=data.get("metadata", {})
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "filename": self.filename,
            "type": self.type,
            "added_at": self.added_at,
            "metadata": self.metadata
        }
    
    def __iter__(self):
        """Make ConversationDTO iterable to prevent runtime errors."""
        # Return an empty iterator by default
        return iter([])

@dataclass
class ConversationDTO:
    """Data Transfer Object for a conversation."""
    
    title: str
    created_at: str
    updated_at: str
    id: Optional[str] = None
    messages: List[MessageDTO] = field(default_factory=list)
    documents: List[DocumentDTO] = field(default_factory=list)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConversationDTO':
        """Create a ConversationDTO from a dictionary."""
        messages = [MessageDTO.from_dict(msg) for msg in data.get("messages", [])]
        documents = [DocumentDTO.from_dict(doc) for doc in data.get("documents", [])]
        
        return cls(
            id=data.get("id"),
            title=data.get("title", "New Conversation"),
            created_at=data.get("created_at", datetime.utcnow().isoformat()),
            updated_at=data.get("updated_at", datetime.utcnow().isoformat()),
            messages=messages,
            documents=documents
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "title": self.title,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "messages": [msg.to_dict() for msg in self.messages],
            "documents": [doc.to_dict() for doc in self.documents]
        }
    
    def __iter__(self):
        """Make ConversationDTO iterable to prevent runtime errors."""
        # Return an empty iterator by default
        return iter([])

@dataclass
class ConversationListItemDTO:
    """Data Transfer Object for a conversation list item (summary)."""
    
    id: str
    title: str
    created_at: str
    updated_at: str
    message_count: int
    document_count: int
    last_message: Optional[MessageDTO] = None
    
    @classmethod
    def from_conversation(cls, conversation: ConversationDTO) -> 'ConversationListItemDTO':
        """Create a ConversationListItemDTO from a ConversationDTO."""
        last_message = None
        if conversation.messages and len(conversation.messages) > 0:
            last_message = conversation.messages[-1]
        
        return cls(
            id=conversation.id,
            title=conversation.title,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
            message_count=len(conversation.messages),
            document_count=len(conversation.documents),
            last_message=last_message
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        result = {
            "id": self.id,
            "title": self.title,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "message_count": self.message_count,
            "document_count": self.document_count
        }
        
        if self.last_message:
            result["last_message"] = self.last_message.to_dict()
        
        return result
    
    def __iter__(self):
        """Make ConversationDTO iterable to prevent runtime errors."""
        # Return an empty iterator by default
        return iter([])
