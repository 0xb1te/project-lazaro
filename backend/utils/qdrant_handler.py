from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.models import Distance, VectorParams
import os
import uuid
import json
from datetime import datetime
from ..config import QDRANT_HOST, QDRANT_PORT, COLLECTION_NAME, CONVERSATIONS_COLLECTION

def get_qdrant_client():
    """Initialize and return Qdrant client."""
    return QdrantClient(
        host=QDRANT_HOST,
        port=QDRANT_PORT
    )

# Vector Embeddings Collection Functions

def init_collection(dimension=384):  # 384 is the dimension for all-MiniLM-L6-v2
    """Initialize Qdrant collection if it doesn't exist."""
    client = get_qdrant_client()
    
    # Check if collection exists
    collections = client.get_collections().collections
    exists = any(col.name == COLLECTION_NAME for col in collections)
    
    if not exists:
        # Create new collection
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(
                size=dimension,
                distance=Distance.COSINE
            )
        )
    
    return client

def insert_documents(texts, embeddings):
    """Insert documents and their embeddings into Qdrant."""
    client = get_qdrant_client()
    
    # Prepare points for insertion
    points = []
    for i, (text, embedding) in enumerate(zip(texts, embeddings)):
        points.append(
            models.PointStruct(
                id=i,
                vector=embedding,
                payload={
                    "text": text.page_content,
                    "metadata": text.metadata
                }
            )
        )
    
    # Insert points in batches
    BATCH_SIZE = 100
    for i in range(0, len(points), BATCH_SIZE):
        batch = points[i:i + BATCH_SIZE]
        client.upsert(
            collection_name=COLLECTION_NAME,
            points=batch
        )

def search_similar_documents(query_vector, limit=200):
    """Search for similar documents using the query vector."""
    client = get_qdrant_client()
    
    # Search for similar vectors
    search_result = client.search(
        collection_name=COLLECTION_NAME,
        query_vector=query_vector,
        limit=limit
    )
    
    # Format results
    results = []
    for scored_point in search_result:
        results.append({
            "text": scored_point.payload["text"],
            "similarity": scored_point.score,
            "metadata": scored_point.payload.get("metadata", {})
        })
    
    return results

def clear_collection():
    """Clear all documents from the collection."""
    client = get_qdrant_client()
    
    try:
        client.delete_collection(collection_name=COLLECTION_NAME)
    except Exception as e:
        # La colección puede no existir todavía, lo que está bien
        pass
        
    init_collection()

# Conversations Collection Functions

def init_conversations_collection():
    """Initialize Qdrant collection for conversations if it doesn't exist."""
    client = get_qdrant_client()
    
    # Check if collection exists
    collections = client.get_collections().collections
    exists = any(col.name == CONVERSATIONS_COLLECTION for col in collections)
    
    if not exists:
        # Create new collection without vectors
        client.create_collection(
            collection_name=CONVERSATIONS_COLLECTION,
            vectors_config=VectorParams(
                size=1,  # Dimensión mínima, ya que no usaremos vectores reales
                distance=Distance.COSINE
            )
        )
    
    return client

def create_conversation(title="Nueva conversación"):
    """Create a new conversation."""
    client = get_qdrant_client()
    init_conversations_collection()
    
    conversation_id = str(uuid.uuid4())
    conversation = {
        "id": conversation_id,
        "title": title,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
        "messages": [
            {
                "role": "system",
                "content": "¡Hola! ¿En qué puedo ayudarte con tu código?",
                "timestamp": datetime.utcnow().isoformat()
            }
        ]
    }
    
    # Usamos un vector dummy ya que Qdrant requiere vectores
    dummy_vector = [0.0]
    
    client.upsert(
        collection_name=CONVERSATIONS_COLLECTION,
        points=[
            models.PointStruct(
                id=conversation_id,
                vector=dummy_vector,
                payload=conversation
            )
        ]
    )
    
    return conversation

def get_conversations():
    """Get all conversations."""
    client = get_qdrant_client()
    init_conversations_collection()
    
    # Scroll through all conversations
    scroll_result = client.scroll(
        collection_name=CONVERSATIONS_COLLECTION,
        limit=200  # Ajusta según necesites
    )
    
    conversations = []
    for point in scroll_result[0]:
        conversations.append(point.payload)
    
    # Ordenar por fecha de actualización (más reciente primero)
    conversations.sort(key=lambda x: x.get('updated_at', ''), reverse=True)
    
    return conversations

def get_conversation(conversation_id):
    """Get a specific conversation by ID."""
    client = get_qdrant_client()
    
    try:
        point = client.retrieve(
            collection_name=CONVERSATIONS_COLLECTION,
            ids=[conversation_id]
        )
        
        if point and len(point) > 0:
            return point[0].payload
        return None
    except Exception as e:
        print(f"Error retrieving conversation: {e}")
        return None

def add_message(conversation_id, role, content):
    """Add a message to a conversation."""
    client = get_qdrant_client()
    
    # Obtener la conversación actual
    conversation = get_conversation(conversation_id)
    if not conversation:
        return None
    
    # Crear el nuevo mensaje
    message = {
        "role": role,
        "content": content,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    # Añadir mensaje a la lista de mensajes
    conversation["messages"].append(message)
    conversation["updated_at"] = datetime.utcnow().isoformat()
    
    # Guardar la conversación actualizada
    client.upsert(
        collection_name=CONVERSATIONS_COLLECTION,
        points=[
            models.PointStruct(
                id=conversation_id,
                vector=[0.0],  # Vector dummy
                payload=conversation
            )
        ]
    )
    
    return message

def delete_conversation(conversation_id):
    """Delete a conversation."""
    client = get_qdrant_client()
    
    try:
        client.delete(
            collection_name=CONVERSATIONS_COLLECTION,
            points_selector=models.PointIdsList(
                points=[conversation_id]
            )
        )
        return True
    except Exception as e:
        print(f"Error deleting conversation: {e}")
        return False

def update_conversation_title(conversation_id, title):
    """Update a conversation's title."""
    client = get_qdrant_client()
    
    # Obtener la conversación actual
    conversation = get_conversation(conversation_id)
    if not conversation:
        return False
    
    # Actualizar el título
    conversation["title"] = title
    conversation["updated_at"] = datetime.utcnow().isoformat()
    
    # Guardar la conversación actualizada
    client.upsert(
        collection_name=CONVERSATIONS_COLLECTION,
        points=[
            models.PointStruct(
                id=conversation_id,
                vector=[0.0],  # Vector dummy
                payload=conversation
            )
        ]
    )
    
    return True