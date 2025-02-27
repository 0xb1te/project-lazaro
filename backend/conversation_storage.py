import os
import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any

class ConversationStorage:
    """
    Handles the storage and retrieval of conversations and their associated documents.
    """
    def __init__(self, storage_dir="./storage"):
        self.storage_dir = storage_dir
        self.conversations_dir = os.path.join(storage_dir, "conversations")
        self.documents_dir = os.path.join(storage_dir, "documents")
        
        # Create directories if they don't exist
        os.makedirs(self.conversations_dir, exist_ok=True)
        os.makedirs(self.documents_dir, exist_ok=True)
    
    def create_conversation(self, title: str = "New Conversation", initial_message: str = None) -> Dict[str, Any]:
        """Create a new conversation with a unique ID"""
        conversation_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        
        # Initialize conversation data structure
        conversation = {
            "id": conversation_id,
            "title": title,
            "created_at": now,
            "updated_at": now,
            "messages": [],
            "documents": []  # Will store document references
        }
        
        # Add initial system message if provided
        if initial_message:
            conversation["messages"].append({
                "role": "system",
                "content": initial_message,
                "timestamp": now
            })
        
        # Save the conversation
        self._save_conversation(conversation_id, conversation)
        
        return conversation
    
    def get_conversation(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Get a conversation by ID"""
        try:
            file_path = os.path.join(self.conversations_dir, f"{conversation_id}.json")
            with open(file_path, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return None
    
    def get_all_conversations(self) -> List[Dict[str, Any]]:
        """Get all conversations, sorted by updated_at (newest first)"""
        conversations = []
        
        for filename in os.listdir(self.conversations_dir):
            if filename.endswith('.json'):
                file_path = os.path.join(self.conversations_dir, filename)
                try:
                    with open(file_path, 'r') as f:
                        conversation = json.load(f)
                        conversations.append(conversation)
                except (json.JSONDecodeError, IOError):
                    continue
        
        # Sort by updated_at (newest first)
        conversations.sort(key=lambda x: x.get('updated_at', ''), reverse=True)
        return conversations
    
    def update_conversation(self, conversation_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update a conversation with new data"""
        conversation = self.get_conversation(conversation_id)
        if not conversation:
            return None
        
        # Update fields
        for key, value in updates.items():
            if key != 'id':  # Don't allow changing the ID
                conversation[key] = value
        
        # Update the timestamp
        conversation["updated_at"] = datetime.utcnow().isoformat()
        
        # Save the updated conversation
        self._save_conversation(conversation_id, conversation)
        
        return conversation
    
    def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a conversation by ID"""
        file_path = os.path.join(self.conversations_dir, f"{conversation_id}.json")
        try:
            os.remove(file_path)
            return True
        except FileNotFoundError:
            return False
    
    def add_message(self, conversation_id: str, role: str, content: str) -> Optional[Dict[str, Any]]:
        """Add a message to a conversation"""
        conversation = self.get_conversation(conversation_id)
        if not conversation:
            return None
        
        # Create message
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Add message to conversation
        conversation["messages"].append(message)
        conversation["updated_at"] = datetime.utcnow().isoformat()
        
        # Save the updated conversation
        self._save_conversation(conversation_id, conversation)
        
        return message
    
    def add_document_to_conversation(self, conversation_id: str, document_info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Associate a document with a conversation"""
        conversation = self.get_conversation(conversation_id)
        if not conversation:
            return None
        
        # Add document reference to conversation
        document_ref = {
            "id": document_info.get("id", str(uuid.uuid4())),
            "filename": document_info.get("filename", "unnamed_document"),
            "added_at": datetime.utcnow().isoformat()
        }
        
        conversation["documents"].append(document_ref)
        conversation["updated_at"] = datetime.utcnow().isoformat()
        
        # Save the updated conversation
        self._save_conversation(conversation_id, conversation)
        
        return document_ref
    
    def get_conversation_documents(self, conversation_id: str) -> List[Dict[str, Any]]:
        """Get all documents associated with a conversation"""
        conversation = self.get_conversation(conversation_id)
        if not conversation:
            return []
        
        return conversation.get("documents", [])
    
    def _save_conversation(self, conversation_id: str, conversation: Dict[str, Any]) -> None:
        """Save a conversation to disk"""
        file_path = os.path.join(self.conversations_dir, f"{conversation_id}.json")
        with open(file_path, 'w') as f:
            json.dump(conversation, f, indent=2)