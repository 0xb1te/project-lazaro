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
        Process a query and generate a response.
        
        Args:
            query_request: The query request containing the question and parameters
            
        Returns:
            QueryResponseDTO containing the response and relevant context
        """
        try:
            # Ensure collection exists if conversation_id is provided
            if query_request.conversation_id:
                try:
                    # This will create the collection if it doesn't exist
                    self.vector_repository.create_conversation_collection(query_request.conversation_id)
                except Exception as e:
                    print(f"Warning: Error ensuring collection exists: {str(e)}")
            
            # Generate embedding for the query
            query_embedding = self.embedding_service.get_embedding(query_request.query)
            
            # First stage: Search for relevant index chunks
            try:
                index_chunks = self.vector_repository.search_similar(
                    query_vector=query_embedding,
                    limit=query_request.max_results,
                    filter_criteria={
                        "document_type": "index",
                        "conversation_id": query_request.conversation_id
                    },
                    collection_name=query_request.conversation_id
                )
            except Exception as e:
                print(f"Warning: Error searching index chunks: {str(e)}")
                index_chunks = []
            
            # Extract relevant file references from index chunks
            relevant_files = set()
            for chunk in index_chunks:
                if chunk.get("metadata", {}).get("chunk_files"):
                    relevant_files.update(chunk["metadata"]["chunk_files"])
            
            # Second stage: Search for specific code chunks
            code_chunks = []
            if relevant_files:
                try:
                    # Search only in the relevant files
                    code_chunks = self.vector_repository.search_similar(
                        query_vector=query_embedding,
                        limit=query_request.max_results,
                        filter_criteria={
                            "filename": {"$in": list(relevant_files)},
                            "document_type": {"$ne": "index"},
                            "conversation_id": query_request.conversation_id
                        },
                        collection_name=query_request.conversation_id
                    )
                except Exception as e:
                    print(f"Warning: Error searching code chunks: {str(e)}")
            
            # If no index chunks were found, try a general search
            if not index_chunks and not code_chunks:
                try:
                    general_chunks = self.vector_repository.search_similar(
                        query_vector=query_embedding,
                        limit=query_request.max_results,
                        filter_criteria={
                            "conversation_id": query_request.conversation_id
                        },
                        collection_name=query_request.conversation_id
                    )
                    code_chunks.extend(general_chunks)
                except Exception as e:
                    print(f"Warning: Error performing general search: {str(e)}")
            
            # Combine and sort results
            all_chunks = []
            
            # Add index chunks with boosted scores
            for chunk in index_chunks:
                chunk["similarity"] *= 1.2  # Boost index relevance by 20%
                all_chunks.append(chunk)
            
            # Add code chunks
            all_chunks.extend(code_chunks)
            
            # Sort by similarity score
            all_chunks.sort(key=lambda x: x["similarity"], reverse=True)
            
            # Limit to max_results
            all_chunks = all_chunks[:query_request.max_results]
            
            # Prepare context for LLM
            context_parts = []
            
            # Add index context first
            index_context = [chunk for chunk in all_chunks if chunk["metadata"].get("document_type") == "index"]
            if index_context:
                context_parts.append("\nProject Context:")
                for chunk in index_context:
                    context_parts.append(f"\n{chunk['text']}")
            
            # Add code context
            code_context = [chunk for chunk in all_chunks if chunk["metadata"].get("document_type") != "index"]
            if code_context:
                context_parts.append("\nRelevant Code:")
                for chunk in code_context:
                    filename = chunk["metadata"].get("filename", "unknown")
                    context_parts.append(f"\nFrom {filename}:\n{chunk['text']}")
            
            # Combine context
            context = "\n".join(context_parts) if context_parts else "No relevant context found."
            
            # Generate response using LLM
            response = self.llm_service.generate_response(
                question=query_request.query,
                context=context,
                temperature=query_request.temperature
            )
            
            # Create response DTO
            return QueryResponseDTO(
                query=query_request.query,
                response=response,
                context=context if query_request.include_context else None,
                chunks=all_chunks if query_request.include_context else None,
                conversation_id=query_request.conversation_id
            )
            
        except Exception as e:
            raise Exception(f"Error processing query: {str(e)}")
    
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
