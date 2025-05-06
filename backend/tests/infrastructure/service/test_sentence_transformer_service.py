import unittest
from unittest.mock import MagicMock, patch
import numpy as np

from backend.infrastructure.service.sentence_transformer_service import SentenceTransformerService
from backend.domain.port.service.embedding_service import EmbeddingService

class TestSentenceTransformerService(unittest.TestCase):
    """Test cases for the SentenceTransformerService."""
    
    @patch('backend.infrastructure.service.sentence_transformer_service.SentenceTransformer')
    def setUp(self, mock_transformer):
        """Set up test fixtures."""
        # Mock the SentenceTransformer
        self.mock_transformer = mock_transformer
        self.mock_model = MagicMock()
        self.mock_transformer.return_value = self.mock_model
        
        # Mock embedding dimension
        self.embedding_dimension = 384
        self.mock_model.get_sentence_embedding_dimension.return_value = self.embedding_dimension
        
        # Create service instance
        self.service = SentenceTransformerService(model_name="test-model")
    
    def test_implements_embedding_service_interface(self):
        """Test that SentenceTransformerService implements the EmbeddingService interface."""
        self.assertIsInstance(self.service, EmbeddingService)
    
    def test_generate_embedding(self):
        """Test generating a single embedding."""
        # Arrange
        test_text = "This is a test"
        expected_embedding = np.random.rand(self.embedding_dimension)
        self.mock_model.encode.return_value = expected_embedding
        
        # Act
        result = self.service.generate_embedding(test_text)
        
        # Assert
        self.mock_model.encode.assert_called_once_with(test_text)
        self.assertEqual(len(result), self.embedding_dimension)
        np.testing.assert_array_equal(result, expected_embedding.tolist())
    
    def test_generate_embeddings(self):
        """Test generating multiple embeddings."""
        # Arrange
        test_texts = ["Text 1", "Text 2", "Text 3"]
        expected_embeddings = np.random.rand(3, self.embedding_dimension)
        self.mock_model.encode.return_value = expected_embeddings
        
        # Act
        result = self.service.generate_embeddings(test_texts)
        
        # Assert
        self.mock_model.encode.assert_called_once_with(test_texts)
        self.assertEqual(len(result), 3)
        for i, embedding in enumerate(result):
            self.assertEqual(len(embedding), self.embedding_dimension)
            np.testing.assert_array_equal(embedding, expected_embeddings[i].tolist())
    
    def test_get_embedding_dimension(self):
        """Test getting the embedding dimension."""
        # Act
        result = self.service.get_embedding_dimension()
        
        # Assert
        self.assertEqual(result, self.embedding_dimension)
        self.mock_model.get_sentence_embedding_dimension.assert_called_once()
    
    def test_normalize_text(self):
        """Test text normalization."""
        # Arrange
        test_cases = [
            # Text with extra whitespace
            ("  This   has  extra   spaces  ", "This has extra spaces"),
            # Text with non-printable characters
            (f"Text with\x00 control\x01 chars", "Text with control chars"),
            # Empty string
            ("", ""),
            # None value
            (None, "")
        ]
        
        # Act & Assert
        for input_text, expected_output in test_cases:
            result = self.service.normalize_text(input_text)
            self.assertEqual(result, expected_output)
    
    def test_compute_similarity(self):
        """Test computing similarity between embeddings."""
        # Arrange
        embedding1 = [1.0, 0.0, 0.0]
        embedding2 = [0.0, 1.0, 0.0]
        
        with patch('backend.infrastructure.service.sentence_transformer_service.util.cos_sim') as mock_cos_sim:
            # Mock the cosine similarity calculation
            mock_cos_sim.return_value = np.array([[0.5]])
            
            # Act
            result = self.service.compute_similarity(embedding1, embedding2)
            
            # Assert
            self.assertEqual(result, 0.5)
            mock_cos_sim.assert_called_once()
    
    def test_empty_text_handling(self):
        """Test handling of empty text."""
        # Arrange
        empty_text = ""
        
        # Act
        result = self.service.generate_embedding(empty_text)
        
        # Assert
        self.assertEqual(len(result), self.embedding_dimension)
        # Should be a zero vector
        self.assertTrue(all(v == 0.0 for v in result))
        
    def test_backward_compatibility(self):
        """Test backward compatibility with the old method names."""
        # Arrange
        test_text = "This is a test"
        test_texts = ["Text 1", "Text 2", "Text 3"]
        expected_embedding = np.random.rand(self.embedding_dimension)
        expected_embeddings = np.random.rand(3, self.embedding_dimension)
        
        # Mock single embedding
        self.mock_model.encode.side_effect = [expected_embedding, expected_embeddings]
        
        # Act - Test both old and new method names
        embedding_result = self.service.get_embedding(test_text)
        embeddings_result = self.service.get_embeddings(test_texts)
        
        # Assert
        self.assertEqual(len(embedding_result), self.embedding_dimension)
        self.assertEqual(len(embeddings_result), 3)

if __name__ == "__main__":
    unittest.main() 
