import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime
import uuid

from src.application.service.conversation_service import ConversationService
from src.domain.model.conversation import Conversation
from src.domain.model.message import Message
from src.domain.model.document import Document
from src.application.dto.conversation_dto import ConversationDTO, MessageDTO, DocumentDTO

class TestConversationService(unittest.TestCase):
    """Test cases for the ConversationService."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create mock repository
        self.mock_repository = MagicMock()
        
        # Create service instance
        self.service = ConversationService(conversation_repository=self.mock_repository)
    
    def test_create_conversation(self):
        """Test creating a new conversation."""
        # Arrange
        title = "Test Conversation"
        initial_message = "Welcome to the conversation"
        created_at = datetime.utcnow()
        
        # Mock repository save method
        self.mock_repository.save.return_value = {
            "id": "test-id",
            "title": title,
            "created_at": created_at.isoformat(),
            "updated_at": created_at.isoformat(),
            "messages": [
                {
                    "role": "system",
                    "content": initial_message,
                    "timestamp": created_at.isoformat()
                }
            ],
            "documents": []
        }
        
        # Act
        result = self.service.create_conversation(title=title, initial_message=initial_message)
        
        # Assert
        self.assertIsInstance(result, ConversationDTO)
        self.assertEqual(result.title, title)
        self.assertEqual(len(result.messages), 1)
        self.assertEqual(result.messages[0].role, "system")
        self.assertEqual(result.messages[0].content, initial_message)
        
        # Verify repository was called
        self.mock_repository.save.assert_called_once()
    
    def test_get_conversation(self):
        """Test retrieving a conversation by ID."""
        # Arrange
        conversation_id = "test-id"
        title = "Test Conversation"
        created_at = datetime.utcnow().isoformat()
        
        # Mock repository find_by_id method
        self.mock_repository.find_by_id.return_value = {
            "id": conversation_id,
            "title": title,
            "created_at": created_at,
            "updated_at": created_at,
            "messages": [],
            "documents": []
        }
        
        # Act
        result = self.service.get_conversation(conversation_id)
        
        # Assert
        self.assertIsInstance(result, ConversationDTO)
        self.assertEqual(result.id, conversation_id)
        self.assertEqual(result.title, title)
        
        # Verify repository was called
        self.mock_repository.find_by_id.assert_called_once_with(conversation_id)
    
    def test_get_conversation_not_found(self):
        """Test retrieving a non-existent conversation."""
        # Arrange
        conversation_id = "non-existent-id"
        
        # Mock repository find_by_id method to return None
        self.mock_repository.find_by_id.return_value = None
        
        # Act
        result = self.service.get_conversation(conversation_id)
        
        # Assert
        self.assertIsNone(result)
        
        # Verify repository was called
        self.mock_repository.find_by_id.assert_called_once_with(conversation_id)
    
    def test_add_user_message(self):
        """Test adding a user message to a conversation."""
        # Arrange
        conversation_id = "test-id"
        message_content = "Hello, this is a test message"
        
        # Mock repository add_message method
        self.mock_repository.add_message.return_value = {
            "id": str(uuid.uuid4()),
            "role": "user",
            "content": message_content,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Act
        result = self.service.add_user_message(conversation_id, message_content)
        
        # Assert
        self.assertIsInstance(result, MessageDTO)
        self.assertEqual(result.role, "user")
        self.assertEqual(result.content, message_content)
        
        # Verify repository was called
        self.mock_repository.add_message.assert_called_once()
        call_args = self.mock_repository.add_message.call_args[0]
        self.assertEqual(call_args[0], conversation_id)
        self.assertEqual(call_args[1]["role"], "user")
        self.assertEqual(call_args[1]["content"], message_content)
    
    def test_delete_conversation(self):
        """Test deleting a conversation."""
        # Arrange
        conversation_id = "test-id"
        
        # Mock repository delete method
        self.mock_repository.delete.return_value = True
        
        # Act
        result = self.service.delete_conversation(conversation_id)
        
        # Assert
        self.assertTrue(result)
        
        # Verify repository was called
        self.mock_repository.delete.assert_called_once_with(conversation_id)
    
    def test_update_conversation_title(self):
        """Test updating a conversation's title."""
        # Arrange
        conversation_id = "test-id"
        old_title = "Old Title"
        new_title = "New Title"
        created_at = datetime.utcnow().isoformat()
        
        # Mock repository find_by_id method
        self.mock_repository.find_by_id.return_value = {
            "id": conversation_id,
            "title": old_title,
            "created_at": created_at,
            "updated_at": created_at,
            "messages": [],
            "documents": []
        }
        
        # Mock repository save method
        self.mock_repository.save.return_value = {
            "id": conversation_id,
            "title": new_title,
            "created_at": created_at,
            "updated_at": created_at,
            "messages": [],
            "documents": []
        }
        
        # Act
        result = self.service.update_conversation_title(conversation_id, new_title)
        
        # Assert
        self.assertIsInstance(result, ConversationDTO)
        self.assertEqual(result.id, conversation_id)
        self.assertEqual(result.title, new_title)
        
        # Verify repository was called
        self.mock_repository.find_by_id.assert_called_once_with(conversation_id)
        self.mock_repository.save.assert_called_once()

if __name__ == "__main__":
    unittest.main() 