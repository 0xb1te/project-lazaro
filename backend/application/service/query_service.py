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
            
            # Step 1: First search for index.md content
            index_chunks = []
            try:
                index_chunks = self.vector_repository.search_similar(
                    query_vector=query_embedding,
                    limit=5,  # Get more index chunks for better context
                    filter_criteria={
                        "is_index": True,
                        "document_type": "index",
                        "conversation_id": query_request.conversation_id
                    },
                    collection_name=query_request.conversation_id
                )
            except Exception as e:
                print(f"Warning: Error searching index chunks: {str(e)}")

            print(f"Index Chunks: {index_chunks} found for query: {query_request.query} and conversation_id: {query_request.conversation_id}")
            
            # Step 2: First LLM Call - Ask AI to identify relevant files from index content
            relevant_files = set()
            if index_chunks:
                # Combine index content for AI analysis
                index_content = "\n".join([chunk["text"] for chunk in index_chunks])
                
                # Create prompt for AI to identify relevant files
                file_analysis_prompt = f"""You are a code analysis expert. Based on the following project index and the user's question, identify which files are most relevant to answering the question.
                Consider the file's purpose, content, and relationships to other files.
                Return ONLY a JSON array of file paths, nothing else.

                User Question: {query_request.query}

                Project Index:
                {index_content}

                Return format: ["file1.py", "file2.js", etc.]"""

                # Log the file analysis prompt
                print(f"\n[AI File Analysis Prompt]\n{file_analysis_prompt}\n")

                # Get AI's file recommendations
                try:
                    file_recommendations = self.llm_service.generate_response(
                        prompt=file_analysis_prompt,
                        temperature=0.1  # Low temperature for more deterministic output
                    )
                    
                    # Log the file recommendations response
                    print(f"\n[AI File Analysis Response]\n{file_recommendations}\n")
                    
                    # Parse the JSON response
                    import json
                    try:
                        recommended_files = json.loads(file_recommendations)
                        if isinstance(recommended_files, list):
                            relevant_files.update(recommended_files)
                            print(f"AI recommended files: {recommended_files}")
                    except json.JSONDecodeError:
                        print("Warning: Could not parse AI's file recommendations")
                except Exception as e:
                    print(f"Warning: Error getting AI file recommendations: {str(e)}")
            
            # Step 3: Search for content in the recommended files
            code_chunks = []
            if relevant_files:
                try:
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
            
            # Step 4: If no relevant files found or no code chunks, fall back to general search
            if not code_chunks:
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
            
            # Step 5: Prepare context for second LLM call
            context_parts = []
            
            # Add index context first
            if index_chunks:
                context_parts.append("\nProject Context:")
                for chunk in index_chunks:
                    context_parts.append(f"\n{chunk['text']}")
            
            # Add code context
            if code_chunks:
                context_parts.append("\nRelevant Code:")
                for chunk in code_chunks:
                    filename = chunk["metadata"].get("filename", "unknown")
                    context_parts.append(f"\nFrom {filename}:\n{chunk['text']}")
            
            # Combine context
            context = "\n".join(context_parts) if context_parts else "No relevant context found."
            
            # Log the question and context for the second LLM call
            print(f"\n[AI Question]\n{query_request.query}\n")
            print(f"\n[AI Context]\n{context}\n")
            
            # Step 6: Second LLM Call - Generate response using the retrieved context
            # Use question parameter to trigger the default prompt template
            response = self.llm_service.generate_response(
                question=query_request.query,
                temperature=query_request.temperature,
                context=context
            )
            
            # Log the final response
            print(f"\n[AI Response]\n{response}\n")
            
            # Create response DTO
            return QueryResponseDTO(
                query=query_request.query,
                response=response,
                context=context if query_request.include_context else None,
                chunks=code_chunks if query_request.include_context else None,
                conversation_id=query_request.conversation_id
            )
            
        except Exception as e:
            print(f"Error processing query: {str(e)}")
            raise
    
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
