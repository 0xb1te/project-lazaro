# src/application/service/query_service.py
import time
from typing import List, Dict, Any, Optional, Tuple

from src.domain.port.repository.vector_repository import VectorRepository
from src.domain.port.service.embedding_service import EmbeddingService
from src.domain.port.service.llm_service import LLMService
from src.application.service.conversation_service import ConversationService
from src.application.dto.query_dto import QueryRequestDTO, QueryResponseDTO, DocumentChunkDTO

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
        conversation_service: ConversationService,
        collection_name: str
    ):
        """
        Initialize the service with dependencies.
        
        Args:
            vector_repository: Repository for vector search
            embedding_service: Service for generating embeddings
            llm_service: Service for generating text responses
            conversation_service: Service for conversation management
            collection_name: Name of the vector collection
        """
        self.vector_repository = vector_repository
        self.embedding_service = embedding_service
        self.llm_service = llm_service
        self.conversation_service = conversation_service
        self.collection_name = collection_name
    
    def process_query(
        self, 
        question: str, 
        conversation_id: Optional[str] = None,
        max_results: int = 5
    ) -> Tuple[str, List[DocumentChunkDTO]]:
        """
        Process a user query using RAG (Retrieval-Augmented Generation).
        
        Args:
            question: The user's question
            conversation_id: Optional ID of the associated conversation
            max_results: Maximum number of results to retrieve
            
        Returns:
            Tuple of (answer, similar_documents)
        """
        start_time = time.time()
        
        # Create a query request DTO
        query_request = QueryRequestDTO(
            question=question,
            conversation_id=conversation_id,
            max_results=max_results
        )
        
        # Step 1: Generate embedding for the question
        question_embedding = self.embedding_service.get_embedding(query_request.question)
        
        # Step 2: Search for similar documents
        similar_docs_data = self.vector_repository.search_similar(
            self.collection_name,
            question_embedding,
            limit=query_request.max_results
        )
        
        # Convert to DTOs
        similar_docs = [DocumentChunkDTO.from_dict(doc) for doc in similar_docs_data]
        
        # Step 3: Extract context from documents
        context = self._create_context_from_documents(similar_docs)
        
        # Step 4: Get conversation history if requested
        conversation_history = None
        if conversation_id:
            # Get recent messages
            messages = self.conversation_service.get_conversation_history(
                conversation_id=conversation_id,
                max_messages=5  # Limit to recent messages to avoid context overload
            )
            
            if messages:
                # Convert to format expected by LLM service
                conversation_history = [
                    {"role": msg.role, "content": msg.content}
                    for msg in messages
                ]
        
        # Step 5: Generate answer using LLM
        answer = self.llm_service.generate_response(
            question=question,
            context=context,
            conversation_history=conversation_history
        )
        
        # Step 6: Store in conversation if conversation_id provided
        if conversation_id:
            # Add user message
            self.conversation_service.add_user_message(conversation_id, question)
            
            # Add assistant message
            self.conversation_service.add_assistant_message(conversation_id, answer)
        
        # Calculate processing time
        processing_time_ms = (time.time() - start_time) * 1000
        
        # Build response
        response = QueryResponseDTO(
            answer=answer,
            similar_documents=similar_docs,
            conversation_id=conversation_id,
            processing_time_ms=processing_time_ms
        )
        
        return answer, similar_docs
    
    def ask_question(self, query_request: QueryRequestDTO) -> QueryResponseDTO:
        """
        High-level method to process a query and return a structured response.
        
        Args:
            query_request: Query request DTO
            
        Returns:
            Query response DTO
        """
        start_time = time.time()
        
        # Process the query
        answer, similar_docs = self.process_query(
            question=query_request.question,
            conversation_id=query_request.conversation_id,
            max_results=query_request.max_results
        )
        
        # Calculate processing time
        processing_time_ms = (time.time() - start_time) * 1000
        
        # Build and return response
        return QueryResponseDTO(
            answer=answer,
            similar_documents=similar_docs,
            conversation_id=query_request.conversation_id,
            processing_time_ms=processing_time_ms
        )
    
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
        
        for i, doc in enumerate(documents):
            # Add document metadata if available
            metadata = doc.metadata
            source_info = ""
            
            if metadata:
                file_name = metadata.get("file_name", "Unknown")
                file_path = metadata.get("file_path", "Unknown")
                source_info = f"Source: {file_path}"
            
            # Add formatted document chunk with source info
            context_parts.append(f"--- Document {i+1} {source_info} ---\n{doc.text}\n")
        
        # Join all parts into a single context string
        return "\n".join(context_parts)