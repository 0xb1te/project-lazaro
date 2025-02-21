# backend/utils/qdrant_handler.py

from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.models import Distance, VectorParams
import os
from ..config import QDRANT_HOST, QDRANT_PORT, COLLECTION_NAME

def get_qdrant_client():
    """Initialize and return Qdrant client."""
    return QdrantClient(
        host=QDRANT_HOST,
        port=QDRANT_PORT
    )

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

def search_similar_documents(query_vector, limit=5):
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
    client.delete_collection(collection_name=COLLECTION_NAME)
    init_collection()