# src/application/service/query_service.py
import time, os, uuid
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

from backend.domain.port.repository.vector_repository import VectorRepository
from backend.domain.port.service.embedding_service import EmbeddingService
from backend.domain.port.service.llm_service import LLMService
from backend.application.service.conversation_service import ConversationService
from backend.application.dto.query_dto import QueryRequestDTO, QueryResponseDTO, DocumentChunkDTO, RetrievedChunkDTO

class QueryService:
    """
    Application service for handling queries and RAG functionality.
    This service implements use cases related to querying the system, orchestrating
    the flow between vector search, LLM generation, and conversation management.
    """
    
    def __init__(
        self, 
        vector_repository: VectorRepository,
        embedding_service: EmbeddingService,
        llm_service: LLMService,
        conversation_service: ConversationService
    ):
        """
        Initialize the service with dependencies.
        
        Args:
            vector_repository: Repository for vector search
            embedding_service: Service for generating embeddings
            llm_service: Service for generating text responses
            conversation_service: Service for conversation management
        """
        self.vector_repository = vector_repository
        self.embedding_service = embedding_service
        self.llm_service = llm_service
        self.conversation_service = conversation_service
    
    def process_query(self, query_request: QueryRequestDTO) -> QueryResponseDTO:
        """
        Process a query and return a structured response.
        
        Args:
            query_request: The query request DTO
            
        Returns:
            Query response DTO with answer and related documents
        """
        start_time = time.time()
        
        # Step 1: Generate embedding for the query
        query_embedding = self.embedding_service.get_embedding(query_request.query)
        
        # Step 2: Search for similar documents - note we don't pass collection_name anymore
        similar_docs_data = self.vector_repository.search_similar(
            query_vector=query_embedding,
            limit=query_request.max_results
        )
        
        # Convert to DTOs
        similar_docs = []
        for doc_data in similar_docs_data:
            doc_dto = DocumentChunkDTO(
                id=doc_data["id"],
                text=doc_data["text"],
                similarity=doc_data["similarity"],
                metadata=doc_data["metadata"]
            )
            similar_docs.append(doc_dto)
        
        # Step 3: Extract context from documents
        context = self._create_context_from_documents(similar_docs)
        
        # Step 4: Get conversation history if requested
        conversation_history = None
        if query_request.conversation_id:
            try:
                # Get recent messages
                message_objects = self.conversation_service.get_conversation_history(
                    conversation_id=query_request.conversation_id,
                    max_messages=10  # Limit to recent messages to avoid context overload
                )
                
                if message_objects and len(message_objects) > 0:
                    # Convert to format expected by LLM service
                    conversation_history = []
                    for msg in message_objects:
                        conversation_history.append({
                            "role": msg.role,
                            "content": msg.content
                        })
            except Exception as e:
                print(f"Error processing conversation history: {str(e)}")
                conversation_history = None
        
        # Step 5: Generate answer using LLM
        answer = self.llm_service.generate_response(
            question=query_request.query,
            context=context,
            conversation_history=conversation_history
        )
        
        # Step 6: Store in conversation if conversation_id provided
        if query_request.conversation_id:
            # Add user message
            self.conversation_service.add_user_message(query_request.conversation_id, query_request.query)
            
            # Add assistant message
            self.conversation_service.add_assistant_message(query_request.conversation_id, answer)
        
        # Calculate processing time
        processing_time_ms = (time.time() - start_time) * 1000
        
        # Convert DocumentChunkDTO to RetrievedChunkDTO for the response
        retrieved_chunks = []
        for doc in similar_docs:
            retrieved_chunk = RetrievedChunkDTO(
                chunk_id=doc.id or str(uuid.uuid4()),
                document_id=doc.metadata.get("document_id", "unknown"),
                content=doc.text,
                metadata=doc.metadata,
                score=doc.similarity
            )
            retrieved_chunks.append(retrieved_chunk)
        
        # Build response
        response = QueryResponseDTO(
            query=query_request.query,
            response=answer,
            conversation_id=query_request.conversation_id,
            retrieved_chunks=retrieved_chunks,
            timestamp=datetime.utcnow()
        )
        
        return response
    
    def ask_question(self, query_request: QueryRequestDTO) -> QueryResponseDTO:
        """
        High-level method to process a query and return a structured response.
        
        Args:
            query_request: Query request DTO
            
        Returns:
            Query response DTO
        """
        # Process the query
        response = self.process_query(query_request)
        
        return response
    
    def _create_context_from_documents(self, documents: List[DocumentChunkDTO]) -> str:
        """
        Create a context string from document chunks.
        
        Args:
            documents: List of document chunks
            
        Returns:
            Formatted context string
        """
        # Join document texts with separators
        context_parts = []
    
        # Group chunks by source file
        chunks_by_file = {}
        for doc in documents:
            file_path = doc.metadata.get("file_path", "Unknown")
            if file_path not in chunks_by_file:
                chunks_by_file[file_path] = []
            chunks_by_file[file_path].append(doc)
        
        # Format chunks by file
        for file_path, chunks in chunks_by_file.items():
            file_name = os.path.basename(file_path)
            context_parts.append(f"--- File: {file_name} ---")
            
            for i, chunk in enumerate(chunks):
                context_parts.append(f"[Chunk {i+1}]\n{chunk.text}\n")
                
            context_parts.append("")  # Add blank line between files
        
        return "\n".join(context_parts)
