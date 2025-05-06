"""
Common pytest fixtures and configuration for tests.
"""
import os
import tempfile
import shutil
import pytest
from typing import Dict, Any, Generator

from src.infrastructure.config import Config
from src.infrastructure.di.container import Container

@pytest.fixture
def temp_dir() -> Generator[str, None, None]:
    """Fixture providing a temporary directory for tests."""
    # Create temp directory
    dir_path = tempfile.mkdtemp()
    try:
        yield dir_path
    finally:
        # Clean up temp directory
        shutil.rmtree(dir_path)

@pytest.fixture
def mock_config() -> Config:
    """Fixture providing a mock configuration for tests."""
    config = Config()
    # Override config properties for tests
    config.DEBUG_MODE = True
    config.STORAGE_DIR = tempfile.mkdtemp()
    config.UPLOAD_FOLDER = tempfile.mkdtemp()
    
    try:
        yield config
    finally:
        # Clean up temporary directories
        shutil.rmtree(config.STORAGE_DIR, ignore_errors=True)
        shutil.rmtree(config.UPLOAD_FOLDER, ignore_errors=True)

@pytest.fixture
def test_container(mock_config: Config) -> Container:
    """Fixture providing a Container with mock configuration."""
    return Container(mock_config)

@pytest.fixture
def test_conversation_data() -> Dict[str, Any]:
    """Fixture providing test conversation data."""
    return {
        "id": "test-conversation-id",
        "title": "Test Conversation",
        "created_at": "2023-06-15T12:30:45.123456",
        "updated_at": "2023-06-15T12:30:45.123456",
        "messages": [
            {
                "role": "system",
                "content": "Welcome to the test conversation",
                "timestamp": "2023-06-15T12:30:45.123456"
            },
            {
                "role": "user",
                "content": "Hello, this is a test message",
                "timestamp": "2023-06-15T12:35:10.654321"
            },
            {
                "role": "assistant",
                "content": "Hello! How can I help you with your test?",
                "timestamp": "2023-06-15T12:35:15.789012"
            }
        ],
        "documents": [
            {
                "id": "test-document-id",
                "filename": "test-document.txt",
                "added_at": "2023-06-15T12:40:20.987654",
                "type": "file",
                "metadata": {
                    "file_type": "text",
                    "extension": ".txt"
                }
            }
        ]
    }

@pytest.fixture
def test_document_data() -> Dict[str, Any]:
    """Fixture providing test document data."""
    return {
        "id": "test-document-id",
        "filename": "test-document.txt",
        "content": "This is a test document with some content for testing.",
        "type": "file",
        "added_at": "2023-06-15T12:40:20.987654",
        "metadata": {
            "file_type": "text",
            "extension": ".txt",
            "size": 55
        }
    } 