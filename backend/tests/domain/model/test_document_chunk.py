import unittest
import uuid
from backend.domain.model.document_chunk import DocumentChunk

class TestDocumentChunk(unittest.TestCase):
    """Test cases for the DocumentChunk domain entity."""
    
    def test_initialization(self):
        """Test basic initialization of DocumentChunk."""
        # Arrange
        content = "Test content"
        metadata = {"key": "value"}
        document_id = str(uuid.uuid4())
        
        # Act
        chunk = DocumentChunk(content=content, metadata=metadata, document_id=document_id)
        
        # Assert
        self.assertEqual(chunk.content, content)
        self.assertEqual(chunk.metadata, metadata)
        self.assertEqual(chunk.document_id, document_id)
        self.assertIsNotNone(chunk.chunk_id)
    
    def test_auto_id_generation(self):
        """Test that chunk_id is automatically generated if not provided."""
        # Arrange & Act
        chunk1 = DocumentChunk(content="Content 1", metadata={}, document_id="doc1")
        chunk2 = DocumentChunk(content="Content 2", metadata={}, document_id="doc1")
        
        # Assert
        self.assertIsNotNone(chunk1.chunk_id)
        self.assertIsNotNone(chunk2.chunk_id)
        self.assertNotEqual(chunk1.chunk_id, chunk2.chunk_id)
    
    def test_metadata_operations(self):
        """Test metadata addition and retrieval."""
        # Arrange
        chunk = DocumentChunk(content="Content", metadata={"initial": "value"}, document_id="doc1")
        
        # Act
        chunk.add_metadata("new_key", "new_value")
        
        # Assert
        self.assertEqual(chunk.get_metadata("initial"), "value")
        self.assertEqual(chunk.get_metadata("new_key"), "new_value")
        self.assertEqual(chunk.get_metadata("non_existent", "default"), "default")
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        # Arrange
        chunk_id = str(uuid.uuid4())
        document_id = str(uuid.uuid4())
        content = "Test content"
        metadata = {"key": "value"}
        embedding = [0.1, 0.2, 0.3]
        
        chunk = DocumentChunk(
            chunk_id=chunk_id,
            document_id=document_id,
            content=content,
            metadata=metadata,
            embedding=embedding
        )
        
        # Act
        result = chunk.to_dict()
        
        # Assert
        self.assertEqual(result["chunk_id"], chunk_id)
        self.assertEqual(result["document_id"], document_id)
        self.assertEqual(result["content"], content)
        self.assertEqual(result["metadata"], metadata)
        self.assertEqual(result["embedding"], embedding)
    
    def test_from_dict(self):
        """Test creation from dictionary."""
        # Arrange
        chunk_id = str(uuid.uuid4())
        document_id = str(uuid.uuid4())
        content = "Test content"
        metadata = {"key": "value"}
        embedding = [0.1, 0.2, 0.3]
        
        data = {
            "chunk_id": chunk_id,
            "document_id": document_id,
            "content": content,
            "metadata": metadata,
            "embedding": embedding
        }
        
        # Act
        chunk = DocumentChunk.from_dict(data)
        
        # Assert
        self.assertEqual(chunk.chunk_id, chunk_id)
        self.assertEqual(chunk.document_id, document_id)
        self.assertEqual(chunk.content, content)
        self.assertEqual(chunk.metadata, metadata)
        self.assertEqual(chunk.embedding, embedding)
        
if __name__ == "__main__":
    unittest.main() 
