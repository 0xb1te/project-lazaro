# src/domain/model/message.py
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, Optional
import uuid

@dataclass
class Message:
    """
    Domain entity representing a message in a conversation.
    Messages can be from the user, the assistant, or the system.
    """
    
    role: str  # 'user', 'assistant', 'system'
    content: str
    timestamp: datetime
    id: str = None
    
    def __post_init__(self):
        """Initialize default values if not provided."""
        # Generate ID if not provided
        if self.id is None:
            self.id = str(uuid.uuid4())
        
        # Ensure datetime objects
        if isinstance(self.timestamp, str):
            self.timestamp = datetime.fromisoformat(self.timestamp)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary representation for serialization.
        
        Returns:
            Dictionary representation of the message
        """
        return {
            "id": self.id,
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        """
        Create a Message instance from a dictionary.
        
        Args:
            data: Dictionary representation of a message
            
        Returns:
            Message instance
        """
        return cls(
            id=data.get("id"),
            role=data.get("role", ""),
            content=data.get("content", ""),
            timestamp=data.get("timestamp", datetime.utcnow().isoformat())
        )
    
    @property
    def is_user(self) -> bool:
        """
        Check if the message is from the user.
        
        Returns:
            True if the message is from the user, False otherwise
        """
        return self.role == "user"
    
    @property
    def is_assistant(self) -> bool:
        """
        Check if the message is from the assistant.
        
        Returns:
            True if the message is from the assistant, False otherwise
        """
        return self.role == "assistant"
    
    @property
    def is_system(self) -> bool:
        """
        Check if the message is a system message.
        
        Returns:
            True if the message is a system message, False otherwise
        """
        return self.role == "system"
    
    @property
    def formatted_timestamp(self) -> str:
        """
        Get a human-readable timestamp.
        
        Returns:
            Formatted timestamp string
        """
        return self.timestamp.strftime("%Y-%m-%d %H:%M:%S")
    
    def __str__(self) -> str:
        """String representation of the message."""
        return f"{self.role}: {self.content[:50]}..."
