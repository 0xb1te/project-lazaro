# src/application/service/conversation_service.py
from datetime import datetime
from typing import List, Dict, Any, Optional
import uuid

from backend.domain.port.repository.conversation_repository import ConversationRepository
from backend.domain.model.conversation import Conversation
from backend.domain.model.message import Message
from backend.domain.model.document import Document
from backend.application.dto.conversation_dto import ConversationDTO, MessageDTO, DocumentDTO, ConversationListItemDTO

class ConversationService:
    """
    Application service for conversation management.
    This service implements use cases related to conversations, delegating
    to the domain model for business logic and the repository for persistence.
    """
    
    def __init__(self, conversation_repository: ConversationRepository):
        """
        Initialize the service with dependencies.
        
        Args:
            conversation_repository: Repository for conversation persistence
        """
        self.conversation_repository = conversation_repository
    
    def create_conversation(self, title: str = "New Conversation", 
                           initial_message: Optional[str] = None) -> ConversationDTO:
        """
        Create a new conversation with optional initial message.
        
        Args:
            title: Title for the new conversation
            initial_message: Optional system message to add initially
            
        Returns:
            DTO with the created conversation data
        """
        # Create domain entity
        now = datetime.utcnow()
        conversation = Conversation(
            title=title,
            created_at=now,
            updated_at=now
        )
        
        # Add initial message if provided
        if initial_message:
            message = Message(
                role="system",
                content=initial_message,
                timestamp=now
            )
            conversation.messages.append(message)
        
        # Save using repository
        saved_conversation = self.conversation_repository.save(conversation.id, conversation.to_dict())
        
        # Convert to DTO and return
        return ConversationDTO.from_dict(saved_conversation)
    
    def get_conversation(self, conversation_id: str) -> Optional[ConversationDTO]:
        """
        Get a conversation by ID.
        
        Args:
            conversation_id: The unique identifier for the conversation
            
        Returns:
            DTO with the conversation data if found, None otherwise
        """
        conversation_data = self.conversation_repository.find_by_id(conversation_id)
        
        if not conversation_data:
            return None
        
        return ConversationDTO.from_dict(conversation_data)
    
    def get_all_conversations(self) -> List[ConversationListItemDTO]:
        conversations_data = self.conversation_repository.find_all()
        
        result = []
        for conversation_data in conversations_data:
            try:
                # Create a ConversationDTO first
                conversation_dto = ConversationDTO.from_dict(conversation_data)
                
                # Get message count with proper checks
                message_count = 0
                last_message = None
                if hasattr(conversation_dto, 'messages'):
                    messages = conversation_dto.messages
                    if isinstance(messages, list):
                        message_count = len(messages)
                        if message_count > 0:
                            last_message = messages[-1]
                
                # Get document count with proper checks
                document_count = 0
                if hasattr(conversation_dto, 'documents'):
                    documents = conversation_dto.documents
                    if isinstance(documents, list):
                        document_count = len(documents)
                
                # Create list item
                list_item = ConversationListItemDTO(
                    id=conversation_dto.id,
                    title=conversation_dto.title,
                    created_at=conversation_dto.created_at,
                    updated_at=conversation_dto.updated_at,
                    message_count=message_count,
                    document_count=document_count,
                    last_message=last_message
                )
                
                result.append(list_item)
            except Exception as e:
                # Log the error and continue with the next conversation
                print(f"Error processing conversation {conversation_data.get('id', 'unknown')}: {str(e)}")
                continue
        
        return result
    
    def update_conversation_title(self, conversation_id: str, title: str) -> Optional[ConversationDTO]:
        """
        Update a conversation's title.
        
        Args:
            conversation_id: The unique identifier for the conversation
            title: The new title
            
        Returns:
            DTO with the updated conversation data if successful, None otherwise
        """
        # Fetch the conversation
        conversation_data = self.conversation_repository.find_by_id(conversation_id)
        if not conversation_data:
            return None
        
        # Update the title
        conversation = Conversation.from_dict(conversation_data)
        conversation.title = title
        conversation.updated_at = datetime.utcnow()
        
        # Save the changes
        updated_data = self.conversation_repository.save(conversation.id, conversation.to_dict())
        
        # Return DTO
        return ConversationDTO.from_dict(updated_data)
    
    def delete_conversation(self, conversation_id: str) -> bool:
        """
        Delete a conversation.
        
        Args:
            conversation_id: The unique identifier for the conversation
            
        Returns:
            True if the conversation was deleted, False otherwise
        """
        return self.conversation_repository.delete(conversation_id)
    
    def add_message(self, conversation_id: str, role: str, content: str) -> Optional[MessageDTO]:
        """
        Add a message to a conversation.
        
        Args:
            conversation_id: The unique identifier for the conversation
            role: The role of the message sender ('user', 'assistant', 'system')
            content: The message content
            
        Returns:
            DTO with the added message data if successful, None otherwise
        """
        # Create message data
        message_data = {
            "id": str(uuid.uuid4()),
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Add to conversation
        result = self.conversation_repository.add_message(conversation_id, message_data)
        
        if not result:
            return None
        
        # Convert to DTO
        return MessageDTO.from_dict(result)
    
    def add_user_message(self, conversation_id: str, content: str) -> Optional[MessageDTO]:
        """
        Add a user message to a conversation.
        
        Args:
            conversation_id: The unique identifier for the conversation
            content: The message content
            
        Returns:
            DTO with the added message data if successful, None otherwise
        """
        return self.add_message(conversation_id, "user", content)
    
    def add_assistant_message(self, conversation_id: str, content: str) -> Optional[MessageDTO]:
        """
        Add an assistant message to a conversation.
        
        Args:
            conversation_id: The unique identifier for the conversation
            content: The message content
            
        Returns:
            DTO with the added message data if successful, None otherwise
        """
        return self.add_message(conversation_id, "assistant", content)
    
    def add_system_message(self, conversation_id: str, content: str) -> Optional[MessageDTO]:
        """
        Add a system message to a conversation.
        
        Args:
            conversation_id: The unique identifier for the conversation
            content: The message content
            
        Returns:
            DTO with the added message data if successful, None otherwise
        """
        return self.add_message(conversation_id, "system", content)
    
    def add_document_to_conversation(self, conversation_id: str, 
                                    document_info: Dict[str, Any]) -> Optional[DocumentDTO]:
        """
        Add a document to a conversation.
        
        Args:
            conversation_id: The unique identifier for the conversation
            document_info: Information about the document
            
        Returns:
            DTO with the added document data if successful, None otherwise
        """
        # Ensure document has an ID
        if "id" not in document_info:
            document_info["id"] = str(uuid.uuid4())
        
        # Add timestamp if not present
        if "added_at" not in document_info:
            document_info["added_at"] = datetime.utcnow().isoformat()
        
        # Add to conversation
        result = self.conversation_repository.add_document(conversation_id, document_info)
        
        if not result:
            return None
        
        # Convert to DTO
        return DocumentDTO.from_dict(result)
    
    def get_conversation_history(self, conversation_id: str, max_messages: int = 10) -> List[MessageDTO]:
        """
        Get the message history for a conversation.
        
        Args:
            conversation_id: The unique identifier for the conversation
            max_messages: Maximum number of recent messages to return
            
        Returns:
            List of message DTOs (most recent last)
        """
        conversation_data = self.conversation_repository.find_by_id(conversation_id)
        
        if not conversation_data:
            return []
        
        # Get messages directly from the dictionary data
        messages_data = conversation_data.get("messages", [])
        
        # Convert each message dictionary to MessageDTO
        messages = []
        for msg_data in messages_data:
            try:
                msg = MessageDTO.from_dict(msg_data)
                messages.append(msg)
            except Exception as e:
                print(f"Error processing message: {str(e)}")
        
        # Return most recent messages
        return messages[-max_messages:] if len(messages) > max_messages else messages
  
    def get_conversation_documents(self, conversation_id: str) -> List[DocumentDTO]:
        """
        Get all documents associated with a conversation.
        
        Args:
            conversation_id: The unique identifier for the conversation
            
        Returns:
            List of document DTOs
        """
        conversation_dto = self.get_conversation(conversation_id)
        
        if not conversation_dto:
            return []
        
        # Ensure documents is a list before returning
        return conversation_dto.documents if hasattr(conversation_dto, 'documents') and isinstance(conversation_dto.documents, list) else []
