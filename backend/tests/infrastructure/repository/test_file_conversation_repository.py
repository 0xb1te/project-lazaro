import unittest
import os
import shutil
import json
import tempfile
from datetime import datetime

from backend.infrastructure.repository.file_conversation_repository import FileConversationRepository
from backend.domain.port.repository.conversation_repository import ConversationRepository

class TestFileConversationRepository(unittest.TestCase):
    """Test cases for the FileConversationRepository."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary directory for test storage
        self.temp_dir = tempfile.mkdtemp()
        self.conversations_dir = os.path.join(self.temp_dir, "conversations")
        
        # Create repository instance
        self.repository = FileConversationRepository(storage_dir=self.temp_dir)
        
        # Test data
        self.test_conversation_id = "test-conversation-id"
        self.test_conversation_data = {
            "id": self.test_conversation_id,
            "title": "Test Conversation",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "messages": [],
            "documents": []
        }
    
    def tearDown(self):
        """Clean up test fixtures."""
        # Remove temporary directory
        shutil.rmtree(self.temp_dir)
    
    def test_implements_repository_interface(self):
        """Test that FileConversationRepository implements the ConversationRepository interface."""
        self.assertIsInstance(self.repository, ConversationRepository)
    
    def test_save_and_find_by_id(self):
        """Test saving and retrieving a conversation."""
        # Act: Save conversation
        saved_data = self.repository.save(
            self.test_conversation_id, 
            self.test_conversation_data
        )
        
        # Assert: Check saved data
        self.assertEqual(saved_data["id"], self.test_conversation_id)
        self.assertEqual(saved_data["title"], self.test_conversation_data["title"])
        
        # Assert: Check file was created
        file_path = os.path.join(self.conversations_dir, f"{self.test_conversation_id}.json")
        self.assertTrue(os.path.exists(file_path))
        
        # Act: Find by ID
        found_data = self.repository.find_by_id(self.test_conversation_id)
        
        # Assert: Check found data
        self.assertEqual(found_data["id"], self.test_conversation_id)
        self.assertEqual(found_data["title"], self.test_conversation_data["title"])
    
    def test_find_by_id_not_found(self):
        """Test finding a non-existent conversation."""
        # Act
        result = self.repository.find_by_id("non-existent-id")
        
        # Assert
        self.assertIsNone(result)
    
    def test_find_all(self):
        """Test finding all conversations."""
        # Arrange: Save multiple conversations
        for i in range(3):
            conversation_id = f"test-conversation-{i}"
            conversation_data = {
                "id": conversation_id,
                "title": f"Test Conversation {i}",
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
                "messages": [],
                "documents": []
            }
            self.repository.save(conversation_id, conversation_data)
        
        # Act
        result = self.repository.find_all()
        
        # Assert
        self.assertEqual(len(result), 3)
        # Check that all saved conversations are found
        conversation_ids = [conv["id"] for conv in result]
        for i in range(3):
            self.assertIn(f"test-conversation-{i}", conversation_ids)
    
    def test_delete(self):
        """Test deleting a conversation."""
        # Arrange: Save a conversation
        self.repository.save(self.test_conversation_id, self.test_conversation_data)
        
        # Act: Delete it
        result = self.repository.delete(self.test_conversation_id)
        
        # Assert
        self.assertTrue(result)
        # Check file was deleted
        file_path = os.path.join(self.conversations_dir, f"{self.test_conversation_id}.json")
        self.assertFalse(os.path.exists(file_path))
        # Check it's not found
        self.assertIsNone(self.repository.find_by_id(self.test_conversation_id))
    
    def test_delete_not_found(self):
        """Test deleting a non-existent conversation."""
        # Act
        result = self.repository.delete("non-existent-id")
        
        # Assert
        self.assertFalse(result)
    
    def test_update(self):
        """Test updating a conversation."""
        # Arrange: Save a conversation
        self.repository.save(self.test_conversation_id, self.test_conversation_data)
        
        # Act: Update it
        updates = {"title": "Updated Title"}
        result = self.repository.update(self.test_conversation_id, updates)
        
        # Assert
        self.assertIsNotNone(result)
        self.assertEqual(result["title"], "Updated Title")
        # Check file was updated
        file_path = os.path.join(self.conversations_dir, f"{self.test_conversation_id}.json")
        with open(file_path, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)
        self.assertEqual(saved_data["title"], "Updated Title")
    
    def test_add_message(self):
        """Test adding a message to a conversation."""
        # Arrange: Save a conversation
        self.repository.save(self.test_conversation_id, self.test_conversation_data)
        
        # Act: Add a message
        message_data = {
            "role": "user",
            "content": "Test message",
            "timestamp": datetime.utcnow().isoformat()
        }
        result = self.repository.add_message(self.test_conversation_id, message_data)
        
        # Assert
        self.assertIsNotNone(result)
        self.assertEqual(result["role"], "user")
        self.assertEqual(result["content"], "Test message")
        
        # Check conversation was updated
        updated_conversation = self.repository.find_by_id(self.test_conversation_id)
        self.assertEqual(len(updated_conversation["messages"]), 1)
        self.assertEqual(updated_conversation["messages"][0]["role"], "user")
        self.assertEqual(updated_conversation["messages"][0]["content"], "Test message")

if __name__ == "__main__":
    unittest.main() 
