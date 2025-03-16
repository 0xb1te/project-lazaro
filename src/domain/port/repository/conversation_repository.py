# src/domain/port/repository/conversation_repository.py
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any

class ConversationRepository(ABC):
    """
    Port (interface) defining operations for conversation persistence.
    This interface allows the domain and application layers to interact with
    conversation storage without knowing the implementation details.
    
    Implementations of this interface might use file storage, databases,
    or other persistence mechanisms.
    """
    
    @abstractmethod
    def save(self, conversation_id: str, conversation_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Save a conversation.
        
        Args:
            conversation_id: The unique identifier for the conversation
            conversation_data: The conversation data to save
            
        Returns:
            The saved conversation data
        """
        pass
    
    @abstractmethod
    def find_by_id(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """
        Find a conversation by ID.
        
        Args:
            conversation_id: The unique identifier for the conversation
            
        Returns:
            The conversation data if found, None otherwise
        """
        pass
    
    @abstractmethod
    def find_all(self) -> List[Dict[str, Any]]:
        """
        Find all conversations.
        
        Returns:
            A list of all conversation data
        """
        pass
    
    @abstractmethod
    def delete(self, conversation_id: str) -> bool:
        """
        Delete a conversation.
        
        Args:
            conversation_id: The unique identifier for the conversation
            
        Returns:
            True if the conversation was deleted, False otherwise
        """
        pass
    
    @abstractmethod
    def update(self, conversation_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Update specific fields of a conversation.
        
        Args:
            conversation_id: The unique identifier for the conversation
            updates: Dictionary containing the fields to update
            
        Returns:
            The updated conversation data if successful, None otherwise
        """
        pass
    
    @abstractmethod
    def add_message(self, conversation_id: str, message_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Add a message to a conversation.
        
        Args:
            conversation_id: The unique identifier for the conversation
            message_data: The message data to add
            
        Returns:
            The added message data if successful, None otherwise
        """
        pass
    
    @abstractmethod
    def add_document(self, conversation_id: str, document_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Add a document reference to a conversation.
        
        Args:
            conversation_id: The unique identifier for the conversation
            document_data: The document data to add
            
        Returns:
            The added document data if successful, None otherwise
        """
        pass