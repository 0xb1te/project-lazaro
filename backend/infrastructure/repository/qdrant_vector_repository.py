# src/infrastructure/repository/qdrant_vector_repository.py
import logging
from typing import List, Dict, Any, Optional, Union
import uuid

from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.models import Distance, VectorParams, PointIdsList, Filter, FieldCondition, MatchValue
from langchain.docstore.document import Document

from backend.domain.port.repository.vector_repository import VectorRepository
from backend.domain.model.document_chunk import DocumentChunk

class QdrantVectorRepository(VectorRepository):
    """
    Qdrant-based implementation of the VectorRepository interface.
    Stores and retrieves document chunks with vector embeddings using Qdrant.
    """
    
    def __init__(self, host: str, port: int, collection_name: str = "documents", embedding_dimension: int = 384, use_per_conversation_collections: bool = True):
        """
        Initialize the repository with Qdrant connection details.
        
        Args:
            host: Qdrant host address
            port: Qdrant port number
            collection_name: Base name for collections
            embedding_dimension: Dimension of the embedding vectors
            use_per_conversation_collections: Whether to use per-conversation collections
        """
        self.host = host
        self.port = port
        self.base_collection_name = collection_name
        self.embedding_dimension = embedding_dimension
        self.use_per_conversation_collections = use_per_conversation_collections
        self.client = QdrantClient(host=host, port=port)
        self.logger = logging.getLogger(__name__)
        
        # Initialize the base collection only if per-conversation collections are disabled
        if not self.use_per_conversation_collections:
            self.initialize_collection(collection_name, embedding_dimension)
    
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
    
    def _get_collection_name(self, conversation_id: str = None) -> str:
        """
        Get the appropriate collection name based on conversation ID.
        
        Args:
            conversation_id: Optional conversation ID
            
        Returns:
            Collection name to use
        """
        if not self.use_per_conversation_collections or not conversation_id:
            return self.base_collection_name
            
        # Format: <uuid>
        return f"{conversation_id}"

    def create_conversation_collection(self, conversation_id: str) -> str:
        """
        Create a new collection for a conversation.
        
        Args:
            conversation_id: ID of the conversation
            
        Returns:
            Name of the created collection
        """
        collection_name = f"{conversation_id}"
        
        # Check if collection exists
        collections = self.client.get_collections().collections
        exists = any(col.name == collection_name for col in collections)
        
        if not exists:
            # Create new collection
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=self.embedding_dimension,
                    distance=Distance.COSINE
                )
            )
            self.logger.info(f"Created new collection: {collection_name}")
        else:
            self.logger.info(f"Collection {collection_name} already exists")
        
        return collection_name

    def list_conversation_collections(self) -> List[str]:
        """
        List all collections associated with conversations.
        
        Returns:
            List of collection names
        """
        collections = self.client.get_collections().collections
        prefix = ""
        return [col.name for col in collections if col.name.startswith(prefix)]

    def delete_conversation_collection(self, conversation_id: str) -> None:
        """
        Delete a collection associated with a conversation.
        
        Args:
            conversation_id: ID of the conversation
        """
        collection_name = f"{conversation_id}"
        self.delete_collection(collection_name)

    def add_documents(self, documents: List[Union[Document, DocumentChunk]], conversation_id: Optional[str] = None) -> None:
        """
        Add documents to the vector store.
        
        Args:
            documents: List of documents to add
            conversation_id: Optional conversation ID to use as collection name
        """
        if not documents:
            return
            
        try:
            # Determine collection name
            collection_name = self._get_collection_name(conversation_id)
            
            # Check if collection exists, if not create it
            try:
                collection_info = self.client.get_collection(collection_name)
                self.logger.debug(f"Found existing collection: {collection_name}")
            except Exception as e:
                self.logger.info(f"Collection {collection_name} does not exist, creating it...")
                self.initialize_collection(collection_name)
            
            # Convert documents to points
            points = []
            for doc in documents:
                # Handle analysis documents (without embeddings) differently
                if isinstance(doc, DocumentChunk) and doc.metadata.get('type') == 'analysis':
                    point = models.PointStruct(
                        id=doc.chunk_id,
                        vector=[0.0] * self.embedding_dimension,  # Dummy vector for analysis docs
                        payload={
                            'content': doc.content,
                            'metadata': doc.metadata,
                            'document_id': doc.document_id
                        }
                    )
                    points.append(point)
                    continue
                
                # Skip other documents without embeddings
                if not hasattr(doc, 'embedding') or doc.embedding is None:
                    continue
                    
                point = models.PointStruct(
                    id=doc.chunk_id if isinstance(doc, DocumentChunk) else str(uuid.uuid4()),
                    vector=doc.embedding,
                    payload={
                        'content': doc.content if isinstance(doc, DocumentChunk) else doc.page_content,
                        'metadata': doc.metadata,
                        'document_id': doc.document_id if isinstance(doc, DocumentChunk) else doc.metadata.get('document_id', str(uuid.uuid4()))
                    }
                )
                points.append(point)
            
            if points:
                # Batch points in groups of 100 to avoid timeouts
                batch_size = 100
                for i in range(0, len(points), batch_size):
                    batch = points[i:i + batch_size]
                    self.client.upsert(
                        collection_name=collection_name,
                        points=batch,
                        wait=True
                    )
                    self.logger.debug(f"Added batch of {len(batch)} points to collection {collection_name}")
                
                self.logger.info(f"Successfully added {len(points)} points to collection {collection_name}")
            else:
                self.logger.warning("No points to add: all documents were skipped (no embeddings)")
                
        except Exception as e:
            self.logger.error(f"Error adding documents to vector store: {str(e)}")
            raise

    def search_similar(self, 
                      query_vector: List[float], 
                      limit: int = 200,
                      filter_criteria: Optional[Dict[str, Any]] = None,
                      collection_name: str = None,
                      conversation_id: str = None) -> List[Dict[str, Any]]:
        """
        Search for document chunks similar to a query vector.
        
        Args:
            query_vector: Vector to search for
            limit: Maximum number of results
            filter_criteria: Optional filter criteria
            collection_name: Name of the collection (optional)
            conversation_id: ID of the conversation (optional)
            
        Returns:
            List of document chunks with similarity scores
        """
        # Determine collection name
        if collection_name is None:
            collection_name = self._get_collection_name(conversation_id)
        
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
        
        try:
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
                # Get text content from the correct field
                text = scored_point.payload.get("content", "")
                if not text:
                    # Fallback to 'text' field for backward compatibility
                    text = scored_point.payload.get("text", "")
                
                results.append({
                    "id": scored_point.id,
                    "text": text,
                    "similarity": scored_point.score,
                    "metadata": scored_point.payload.get("metadata", {}),
                    "document_id": scored_point.payload.get("document_id")
                })
            
            self.logger.info(f"Found {len(results)} results in collection {collection_name}")
            return results
            
        except Exception as e:
            self.logger.error(f"Error searching similar vectors: {str(e)}")
            raise
    
    def clear_collection(self, collection_name: str = None) -> None:
        """
        Clear all documents from a collection.
        
        Args:
            collection_name: Name of the collection (optional, uses default if not specified)
        """
        # Use default collection if not specified
        collection_name = collection_name or self.base_collection_name
        
        try:
            # Delete the collection
            self.client.delete_collection(collection_name=collection_name)
            self.logger.info(f"Deleted collection {collection_name}")
            
            # Recreate it
            self.initialize_collection(collection_name, self.embedding_dimension)
            self.logger.info(f"Recreated empty collection {collection_name}")
        except Exception as e:
            # The collection might not exist, which is fine
            self.logger.warning(f"Error clearing collection {collection_name}: {str(e)}")
            
            # Ensure the collection exists
            self.initialize_collection(collection_name, self.embedding_dimension)
    
    def delete_collection(self, collection_name: str = None) -> None:
        """
        Delete a collection.
        
        Args:
            collection_name: Name of the collection (optional, uses default if not specified)
        """
        # Use default collection if not specified
        collection_name = collection_name or self.base_collection_name
        
        try:
            self.client.delete_collection(collection_name=collection_name)
            self.logger.info(f"Deleted collection {collection_name}")
        except Exception as e:
            self.logger.warning(f"Error deleting collection {collection_name}: {str(e)}")
    
    def get_collection_info(self, collection_name: str = None) -> Dict[str, Any]:
        """
        Get information about a collection.
        
        Args:
            collection_name: Name of the collection (optional, uses default if not specified)
            
        Returns:
            Dictionary with collection information
        """
        # Use default collection if not specified
        collection_name = collection_name or self.base_collection_name
        
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
    
    def get_document_by_id(self, document_id: str, collection_name: str = None) -> Optional[Dict[str, Any]]:
        """
        Get a document by ID.
        
        Args:
            document_id: ID of the document
            collection_name: Name of the collection (optional, uses default if not specified)
            
        Returns:
            Document data if found, None otherwise
        """
        # Use default collection if not specified
        collection_name = collection_name or self.base_collection_name
        
        try:
            # Retrieve points by ID
            points = self.client.retrieve(
                collection_name=collection_name,
                ids=[document_id]
            )
            
            if not points:
                return None
            
            point = points[0]
            
            # Format result
            result = {
                "id": point.id,
                "text": point.payload["text"],
                "metadata": point.payload.get("metadata", {})
            }
            
            return result
        except Exception as e:
            self.logger.warning(f"Error retrieving document {document_id}: {str(e)}")
            return None
    
    def delete_documents(self, document_ids: List[str], collection_name: str = None) -> int:
        """
        Delete documents from a collection.
        
        Args:
            document_ids: List of document IDs to delete
            collection_name: Name of the collection (optional, uses default if not specified)
            
        Returns:
            Number of documents deleted
        """
        # Use default collection if not specified
        collection_name = collection_name or self.base_collection_name
        
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
                        metadata_filter: Dict[str, Any],
                        limit: int = 200,
                        collection_name: str = None) -> List[Dict[str, Any]]:
        """
        Search for documents by metadata criteria.
        
        Args:
            metadata_filter: Dictionary with metadata key-value pairs to match
            limit: Maximum number of results
            collection_name: Name of the collection (optional, uses default if not specified)
            
        Returns:
            List of document chunks matching the criteria
        """
        # Use default collection if not specified
        collection_name = collection_name or self.base_collection_name
        
        try:
            # Prepare filter
            filter_conditions = []
            
            for key, value in metadata_filter.items():
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
            
            # Search for matching documents
            search_result = self.client.scroll(
                collection_name=collection_name,
                scroll_filter=search_filter,
                limit=limit
            )
            
            # Format results
            results = []
            for point in search_result[0]:
                results.append({
                    "id": point.id,
                    "content": point.payload.get("content", ""),
                    "metadata": point.payload.get("metadata", {})
                })
            
            self.logger.info(f"Found {len(results)} documents matching metadata filter")
            return results
        except Exception as e:
            self.logger.warning(f"Error searching by metadata: {str(e)}")
            return []
