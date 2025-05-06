"""
Integration tests for the Flask API.
"""
import pytest
import json
import io
from typing import Dict, Any

from src.infrastructure.api.flask_app import FlaskApiAdapter
from src.infrastructure.config import Config

@pytest.fixture
def app_client(mock_config: Config):
    """Fixture providing a Flask test client."""
    adapter = FlaskApiAdapter(mock_config)
    app = adapter.get_app()
    app.config['TESTING'] = True
    
    with app.test_client() as client:
        yield client

def test_health_check(app_client):
    """Test the health check endpoint."""
    # Act
    response = app_client.get('/')
    data = json.loads(response.data)
    
    # Assert
    assert response.status_code == 200
    assert data['status'] == 'healthy'
    assert 'environment' in data

def test_create_conversation(app_client):
    """Test creating a new conversation."""
    # Arrange
    payload = {
        "title": "Test Conversation",
        "initial_message": "Welcome to the test conversation"
    }
    
    # Act
    response = app_client.post(
        '/conversations',
        data=json.dumps(payload),
        content_type='application/json'
    )
    data = json.loads(response.data)
    
    # Assert
    assert response.status_code == 201
    assert data['title'] == payload['title']
    assert len(data['messages']) == 1
    assert data['messages'][0]['role'] == 'system'
    assert data['messages'][0]['content'] == payload['initial_message']

def test_get_conversation_not_found(app_client):
    """Test retrieving a non-existent conversation."""
    # Act
    response = app_client.get('/conversations/non-existent-id')
    data = json.loads(response.data)
    
    # Assert
    assert response.status_code == 404
    assert 'error' in data

def test_create_and_get_conversation(app_client):
    """Test creating and then retrieving a conversation."""
    # Arrange - Create a conversation
    create_payload = {
        "title": "Test Conversation for Retrieval",
        "initial_message": "Welcome to the conversation"
    }
    create_response = app_client.post(
        '/conversations',
        data=json.dumps(create_payload),
        content_type='application/json'
    )
    create_data = json.loads(create_response.data)
    conversation_id = create_data['id']
    
    # Act - Get the conversation
    response = app_client.get(f'/conversations/{conversation_id}')
    data = json.loads(response.data)
    
    # Assert
    assert response.status_code == 200
    assert data['id'] == conversation_id
    assert data['title'] == create_payload['title']

def test_add_message_to_conversation(app_client):
    """Test adding a message to a conversation."""
    # Arrange - Create a conversation
    create_response = app_client.post(
        '/conversations',
        data=json.dumps({"title": "Test Conversation"}),
        content_type='application/json'
    )
    conversation_id = json.loads(create_response.data)['id']
    
    # Arrange - Message payload
    message_payload = {
        "role": "user",
        "content": "This is a test message"
    }
    
    # Act - Add message
    response = app_client.post(
        f'/conversations/{conversation_id}/messages',
        data=json.dumps(message_payload),
        content_type='application/json'
    )
    data = json.loads(response.data)
    
    # Assert
    assert response.status_code == 200
    assert data['role'] == message_payload['role']
    assert data['content'] == message_payload['content']
    
    # Verify message was added to conversation
    get_response = app_client.get(f'/conversations/{conversation_id}')
    get_data = json.loads(get_response.data)
    assert len(get_data['messages']) > 0
    user_messages = [m for m in get_data['messages'] if m['role'] == 'user']
    assert len(user_messages) == 1
    assert user_messages[0]['content'] == message_payload['content']

def test_delete_conversation(app_client):
    """Test deleting a conversation."""
    # Arrange - Create a conversation
    create_response = app_client.post(
        '/conversations',
        data=json.dumps({"title": "Conversation to Delete"}),
        content_type='application/json'
    )
    conversation_id = json.loads(create_response.data)['id']
    
    # Act - Delete the conversation
    response = app_client.delete(f'/conversations/{conversation_id}')
    data = json.loads(response.data)
    
    # Assert
    assert response.status_code == 200
    assert data['success'] is True
    
    # Verify conversation was deleted
    get_response = app_client.get(f'/conversations/{conversation_id}')
    assert get_response.status_code == 404

def test_get_all_conversations(app_client):
    """Test retrieving all conversations."""
    # Arrange - Create a few conversations
    for i in range(3):
        app_client.post(
            '/conversations',
            data=json.dumps({"title": f"Test Conversation {i}"}),
            content_type='application/json'
        )
    
    # Act
    response = app_client.get('/conversations')
    data = json.loads(response.data)
    
    # Assert
    assert response.status_code == 200
    assert isinstance(data, list)
    assert len(data) >= 3  # At least the 3 we just created
    # Check titles of created conversations are present
    titles = [conv['title'] for conv in data]
    for i in range(3):
        assert f"Test Conversation {i}" in titles

def test_update_conversation(app_client):
    """Test updating a conversation."""
    # Arrange - Create a conversation
    create_response = app_client.post(
        '/conversations',
        data=json.dumps({"title": "Original Title"}),
        content_type='application/json'
    )
    conversation_id = json.loads(create_response.data)['id']
    
    # Act - Update the title
    update_payload = {"title": "Updated Title"}
    response = app_client.put(
        f'/conversations/{conversation_id}',
        data=json.dumps(update_payload),
        content_type='application/json'
    )
    data = json.loads(response.data)
    
    # Assert
    assert response.status_code == 200
    assert data['title'] == update_payload['title']
    
    # Verify conversation was updated
    get_response = app_client.get(f'/conversations/{conversation_id}')
    get_data = json.loads(get_response.data)
    assert get_data['title'] == update_payload['title'] 