# src/infrastructure/repository/file_conversation_repository.py
import os
import json
from typing import List, Dict, Any, Optional
from datetime import datetime

from backend.domain.port.repository.conversation_repository import ConversationRepository

class FileConversationRepository(ConversationRepository):
    """
    File-based implementation of the ConversationRepository interface.
    Stores conversations as JSON files in the filesystem.
    """
    
    def __init__(self, storage_dir: str):
        """
        Initialize the repository with the storage directory.
        
        Args:
            storage_dir: Directory where conversations will be stored
        """
        self.storage_dir = storage_dir
        self.conversations_dir = os.path.join(storage_dir, "conversations")
        
        # Create directories if they don't exist
        os.makedirs(self.conversations_dir, exist_ok=True)
    
    def save(self, conversation_id: str, conversation_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Save a conversation to a file.
        
        Args:
            conversation_id: The unique identifier for the conversation
            conversation_data: The conversation data to save
            
        Returns:
            The saved conversation data
        """
        file_path = os.path.join(self.conversations_dir, f"{conversation_id}.json")
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(conversation_data, f, indent=2, ensure_ascii=False)
        
        return conversation_data
    
    def find_by_id(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """
        Find a conversation by ID.
        
        Args:
            conversation_id: The unique identifier for the conversation
            
        Returns:
            The conversation data if found, None otherwise
        """
        file_path = os.path.join(self.conversations_dir, f"{conversation_id}.json")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return None
    
    def find_all(self) -> List[Dict[str, Any]]:
        """
        Find all conversations.
        
        Returns:
            A list of all conversation data
        """
        conversations = []
        
        for filename in os.listdir(self.conversations_dir):
            if filename.endswith('.json'):
                file_path = os.path.join(self.conversations_dir, filename)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        conversation = json.load(f)
                        conversations.append(conversation)
                except (json.JSONDecodeError, IOError):
                    # Skip files with errors
                    continue
        
        # Sort by updated_at (newest first)
        conversations.sort(key=lambda x: x.get('updated_at', ''), reverse=True)
        return conversations
    
    def delete(self, conversation_id: str) -> bool:
        """
        Delete a conversation and its associated vector collection.
        
        Args:
            conversation_id: The unique identifier for the conversation
            
        Returns:
            True if the conversation was deleted, False otherwise
        """
        file_path = os.path.join(self.conversations_dir, f"{conversation_id}.json")
        
        try:
            # Delete the conversation file
            os.remove(file_path)
            
            # Delete the associated vector collection
            try:
                from backend.infrastructure.di.container import Container
                from backend.infrastructure.config import Config
                
                # Get vector repository instance
                config = Config()
                container = Container(config)
                vector_repository = container.get_vector_repository()
                
                # Delete the conversation collection
                vector_repository.delete_collection(conversation_id)
                print(f"Deleted vector collection: {conversation_id}")
            except Exception as e:
                print(f"Error deleting vector collection: {str(e)}")
                # Continue even if collection deletion fails
            
            return True
        except FileNotFoundError:
            return False
    
    def update(self, conversation_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Update specific fields of a conversation.
        
        Args:
            conversation_id: The unique identifier for the conversation
            updates: Dictionary containing the fields to update
            
        Returns:
            The updated conversation data if successful, None otherwise
        """
        # Get existing conversation
        conversation = self.find_by_id(conversation_id)
        if not conversation:
            return None
        
        # Apply updates
        for key, value in updates.items():
            if key != 'id':  # Don't allow changing the ID
                conversation[key] = value
        
        # Update the timestamp
        conversation["updated_at"] = datetime.utcnow().isoformat()
        
        # Save the updated conversation
        return self.save(conversation_id, conversation)
    
    def add_message(self, conversation_id: str, message_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Add a message to a conversation.
        
        Args:
            conversation_id: The unique identifier for the conversation
            message_data: The message data to add
            
        Returns:
            The added message data if successful, None otherwise
        """
        # Get existing conversation
        conversation = self.find_by_id(conversation_id)
        if not conversation:
            return None
        
        # Initialize messages array if it doesn't exist
        if "messages" not in conversation:
            conversation["messages"] = []
        
        # Ensure the message has a timestamp
        if "timestamp" not in message_data:
            message_data["timestamp"] = datetime.utcnow().isoformat()
        
        # Check for duplicate messages (same content and role within a 5-second window)
        current_time = datetime.fromisoformat(message_data["timestamp"])
        for existing_message in reversed(conversation["messages"]):  # Check most recent messages first
            if (existing_message.get("content") == message_data.get("content") and
                existing_message.get("role") == message_data.get("role")):
                existing_time = datetime.fromisoformat(existing_message["timestamp"])
                time_diff = abs((current_time - existing_time).total_seconds())
                if time_diff < 5:  # 5-second window
                    print(f"Duplicate message detected within {time_diff:.2f} seconds")
                    return existing_message
        
        # Add message to the conversation
        conversation["messages"].append(message_data)
        
        # Update the conversation timestamp
        conversation["updated_at"] = datetime.utcnow().isoformat()
        
        # Save the updated conversation
        self.save(conversation_id, conversation)
        
        return message_data
    
    def add_document(self, conversation_id: str, document_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Add a document reference to a conversation.
        
        Args:
            conversation_id: The unique identifier for the conversation
            document_data: The document data to add
            
        Returns:
            The added document data if successful, None otherwise
        """
        # Get existing conversation
        conversation = self.find_by_id(conversation_id)
        if not conversation:
            return None
        
        # Initialize documents array if it doesn't exist
        if "documents" not in conversation:
            conversation["documents"] = []
        
        # Ensure the document has an added_at timestamp
        if "added_at" not in document_data:
            document_data["added_at"] = datetime.utcnow().isoformat()
        
        # Add document to the conversation
        conversation["documents"].append(document_data)
        
        # Update the conversation timestamp
        conversation["updated_at"] = datetime.utcnow().isoformat()
        
        # Save the updated conversation
        self.save(conversation_id, conversation)
        
        return document_data
