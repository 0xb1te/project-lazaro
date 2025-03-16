# src/infrastructure/repository/qdrant_vector_repository.py
import logging
from typing import List, Dict, Any, Optional

from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.models import Distance, VectorParams, PointIdsList, Filter, FieldCondition, MatchValue

from src.domain.port.repository.vector_repository import VectorRepository
from src.domain.model.document_chunk import DocumentChunk

class QdrantVectorRepository(VectorRepository):
    """
    Qdrant-based implementation of the VectorRepository interface.
    Stores and retrieves document chunks with vector embeddings using Qdrant.
    """
    
    def __init__(self, host: str, port: int):
        """
        Initialize the repository with Qdrant connection details.
        
        Args:
            host: Qdrant host address
            port: Qdrant port number
        """
        self.host = host
        self.port = port
        self.client = QdrantClient(host=host, port=port)
        self.logger = logging.getLogger(__name__)
    
    def initialize_collection(self, collection_name: str, dimension: int = 384) -> None:
        """
        Initialize a vector collection in Qdrant.
        
        Args:
            collection_name: Name of the collection
            dimension: Dimension of the vectors (384 is typical for all-MiniLM-L6-v2)
        """
        # Check if collection exists
        collections = self.client.get_collections().collections
        exists = any(col.name == collection_name for col in collections)
        
        if not exists:
            # Create new collection
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=dimension,
                    distance=Distance.COSINE
                )
            )
            self.logger.info(f"Created new collection: {collection_name} with dimension {dimension}")
        else:
            self.logger.info(f"Collection {collection_name} already exists")
    
    def add_documents(self, collection_name: str, document_chunks: List[DocumentChunk]) -> List[str]:
        """
        Add document chunks with embeddings to Qdrant.
        
        Args:
            collection_name: Name of the collection
            document_chunks: List of document chunks with embeddings
            
        Returns:
            List of IDs of the added documents
        """
        # Prepare points for insertion
        points = []
        ids = []
        
        for chunk in document_chunks:
            # Skip chunks without embeddings
            if chunk.embedding is None:
                self.logger.warning(f"Skipping chunk with no embedding: {chunk.id}")
                continue
            
            chunk_id = chunk.id
            ids.append(chunk_id)
            
            points.append(
                models.PointStruct(
                    id=chunk_id,
                    vector=chunk.embedding,
                    payload={
                        "text": chunk.content,
                        "metadata": chunk.metadata
                    }
                )
            )
        
        # Insert points in batches
        BATCH_SIZE = 100
        for i in range(0, len(points), BATCH_SIZE):
            batch = points[i:i + BATCH_SIZE]
            self.client.upsert(
                collection_name=collection_name,
                points=batch
            )
        
        self.logger.info(f"Added {len(points)} document chunks to collection {collection_name}")
        return ids
    
    def search_similar(self, 
                      collection_name: str, 
                      query_vector: List[float], 
                      limit: int = 5,
                      filter_criteria: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Search for document chunks similar to a query vector.
        
        Args:
            collection_name: Name of the collection
            query_vector: Vector to search for
            limit: Maximum number of results
            filter_criteria: Optional filter criteria
            
        Returns:
            List of document chunks with similarity scores
        """
        # Prepare search filter if provided
        search_filter = None
        if filter_criteria:
            filter_conditions = []
            
            for key, value in filter_criteria.items():
                if key.startswith('metadata.'):
                    # For metadata fields, we need to use a special syntax
                    metadata_key = key.replace('metadata.', '')
                    filter_conditions.append(
                        FieldCondition(
                            key=f"metadata.{metadata_key}",
                            match=MatchValue(value=value)
                        )
                    )
                else:
                    # For top-level fields
                    filter_conditions.append(
                        FieldCondition(
                            key=key,
                            match=MatchValue(value=value)
                        )
                    )
            
            # Create the final filter
            search_filter = Filter(
                must=filter_conditions
            )
        
        # Search for similar vectors
        search_result = self.client.search(
            collection_name=collection_name,
            query_vector=query_vector,
            limit=limit,
            query_filter=search_filter
        )
        
        # Format results
        results = []
        for scored_point in search_result:
            results.append({
                "id": scored_point.id,
                "text": scored_point.payload["text"],
                "similarity": scored_point.score,
                "metadata": scored_point.payload.get("metadata", {})
            })
        
        self.logger.info(f"Found {len(results)} results in collection {collection_name}")
        return results
    
    def clear_collection(self, collection_name: str) -> None:
        """
        Clear all documents from a collection.
        
        Args:
            collection_name: Name of the collection
        """
        try:
            # Delete the collection
            self.client.delete_collection(collection_name=collection_name)
            self.logger.info(f"Deleted collection {collection_name}")
            
            # Recreate it
            self.initialize_collection(collection_name)
            self.logger.info(f"Recreated empty collection {collection_name}")
        except Exception as e:
            # The collection might not exist, which is fine
            self.logger.warning(f"Error clearing collection {collection_name}: {str(e)}")
            
            # Ensure the collection exists
            self.initialize_collection(collection_name)
    
    def delete_collection(self, collection_name: str) -> None:
        """
        Delete a collection.
        
        Args:
            collection_name: Name of the collection
        """
        try:
            self.client.delete_collection(collection_name=collection_name)
            self.logger.info(f"Deleted collection {collection_name}")
        except Exception as e:
            self.logger.warning(f"Error deleting collection {collection_name}: {str(e)}")
    
    def get_collection_info(self, collection_name: str) -> Dict[str, Any]:
        """
        Get information about a collection.
        
        Args:
            collection_name: Name of the collection
            
        Returns:
            Dictionary with collection information
        """
        try:
            # Get collection info
            collection_info = self.client.get_collection(collection_name=collection_name)
            
            # Format the result
            info = {
                "name": collection_info.name,
                "vectors_count": collection_info.vectors_count,
                "points_count": collection_info.points_count,
                "dimension": collection_info.config.params.vectors.size,
                "distance": str(collection_info.config.params.vectors.distance),
                "status": collection_info.status
            }
            
            return info
        except Exception as e:
            self.logger.warning(f"Error getting info for collection {collection_name}: {str(e)}")
            return {"name": collection_name, "error": str(e)}
    
    def get_document_by_id(self, collection_name: str, document_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a document by ID.
        
        Args:
            collection_name: Name of the collection
            document_id: ID of the document
            
        Returns:
            Document data if found, None otherwise
        """
        try:
            # Retrieve points by ID
            points = self.client.retrieve(
                collection_name=collection_name,
                ids=[document_id]
            )
            
            if points and len(points) > 0:
                point = points[0]
                return {
                    "id": point.id,
                    "text": point.payload["text"],
                    "metadata": point.payload.get("metadata", {})
                }
            
            return None
        except Exception as e:
            self.logger.warning(f"Error retrieving document {document_id}: {str(e)}")
            return None
    
    def delete_documents(self, collection_name: str, document_ids: List[str]) -> int:
        """
        Delete documents by ID.
        
        Args:
            collection_name: Name of the collection
            document_ids: List of document IDs to delete
            
        Returns:
            Number of documents deleted
        """
        try:
            # Delete points by ID
            self.client.delete(
                collection_name=collection_name,
                points_selector=PointIdsList(
                    points=document_ids
                )
            )
            
            self.logger.info(f"Deleted {len(document_ids)} documents from collection {collection_name}")
            return len(document_ids)
        except Exception as e:
            self.logger.warning(f"Error deleting documents: {str(e)}")
            return 0
    
    def search_by_metadata(self, 
                          collection_name: str, 
                          metadata_filter: Dict[str, Any],
                          limit: int = 100) -> List[Dict[str, Any]]:
        """
        Search for documents by metadata.
        
        Args:
            collection_name: Name of the collection
            metadata_filter: Filter criteria for metadata
            limit: Maximum number of results
            
        Returns:
            List of documents matching the metadata filter
        """
        # Create filter conditions
        filter_conditions = []
        
        for key, value in metadata_filter.items():
            # For metadata fields, we need to use a special syntax
            filter_conditions.append(
                FieldCondition(
                    key=f"metadata.{key}",
                    match=MatchValue(value=value)
                )
            )
        
        # Create the final filter
        search_filter = Filter(
            must=filter_conditions
        )
        
        # Scroll through results
        try:
            scroll_result = self.client.scroll(
                collection_name=collection_name,
                filter=search_filter,
                limit=limit
            )
            
            # Format results
            results = []
            
            for point in scroll_result[0]:
                results.append({
                    "id": point.id,
                    "text": point.payload["text"],
                    "metadata": point.payload.get("metadata", {})
                })
            
            self.logger.info(f"Found {len(results)} documents matching metadata filter")
            return results
        except Exception as e:
            self.logger.warning(f"Error searching by metadata: {str(e)}")
            return []