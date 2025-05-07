# src/domain/model/conversation.py
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional
import uuid

from .message import Message
from .document import Document

@dataclass
class Conversation:
    """
    Domain entity representing a conversation between a user and the assistant.
    A conversation contains messages and references to documents.
    """
    
    title: str
    created_at: datetime
    updated_at: datetime
    id: str = None
    messages: List[Message] = field(default_factory=list)
    documents: List[Document] = field(default_factory=list)
    
    def __post_init__(self):
        """Initialize default values if not provided."""
        # Generate ID if not provided
        if self.id is None:
            self.id = str(uuid.uuid4())
        
        # Ensure datetime objects
        if isinstance(self.created_at, str):
            self.created_at = datetime.fromisoformat(self.created_at)
        if isinstance(self.updated_at, str):
            self.updated_at = datetime.fromisoformat(self.updated_at)
    
    def add_message(self, role: str, content: str) -> Message:
        """
        Add a new message to the conversation.
        
        Args:
            role: The role of the message sender (user, assistant, system)
            content: The message content
            
        Returns:
            The created message
        """
        message = Message(
            role=role,
            content=content,
            timestamp=datetime.utcnow()
        )
        self.messages.append(message)
        self.updated_at = datetime.utcnow()
        return message
    
    def add_document(self, filename: str, doc_type: str = "file", metadata: Dict[str, Any] = None) -> Document:
        """
        Add a document reference to the conversation.
        
        Args:
            filename: Name of the document file
            doc_type: Type of document (file, zip, etc.)
            metadata: Additional metadata about the document
            
        Returns:
            The created document reference
        """
        document = Document(
            filename=filename,
            type=doc_type,
            added_at=datetime.utcnow(),
            metadata=metadata or {}
        )
        self.documents.append(document)
        self.updated_at = datetime.utcnow()
        return document
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary representation for serialization.
        
        Returns:
            Dictionary representation of the conversation
        """
        return {
            "id": self.id,
            "title": self.title,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "messages": [message.to_dict() for message in self.messages],
            "documents": [document.to_dict() for document in self.documents]
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Conversation':
        """
        Create a Conversation instance from a dictionary.
        
        Args:
            data: Dictionary representation of a conversation
            
        Returns:
            Conversation instance
        """
        # Create the conversation object
        conversation = cls(
            id=data.get("id"),
            title=data.get("title", "New Conversation"),
            created_at=data.get("created_at", datetime.utcnow().isoformat()),
            updated_at=data.get("updated_at", datetime.utcnow().isoformat())
        )
        
        # Add messages
        for message_data in data.get("messages", []):
            # If message_data is a dict, convert to Message
            if isinstance(message_data, dict):
                message = Message.from_dict(message_data)
                conversation.messages.append(message)
            # If message_data is already a Message, add directly
            elif isinstance(message_data, Message):
                conversation.messages.append(message_data)
        
        # Add documents
        for document_data in data.get("documents", []):
            # If document_data is a dict, convert to Document
            if isinstance(document_data, dict):
                document = Document.from_dict(document_data)
                conversation.documents.append(document)
            # If document_data is already a Document, add directly
            elif isinstance(document_data, Document):
                conversation.documents.append(document_data)
        
        return conversation
