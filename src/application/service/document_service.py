# src/application/service/document_service.py
import os
import uuid
import tempfile
import zipfile
import time
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

from src.domain.port.repository.vector_repository import VectorRepository
from src.domain.port.service.embedding_service import EmbeddingService
from src.domain.model.document_chunk import DocumentChunk
from src.application.service.conversation_service import ConversationService
from src.application.dto.query_dto import DocumentUploadRequestDTO, DocumentUploadResponseDTO
from src.application.dto.conversation_dto import DocumentDTO

class DocumentService:
    """
    Application service for document processing and management.
    This service implements use cases related to documents, coordinating
    between file processing, vector storage, and conversation management.
    """
    
    def __init__(
        self,
        vector_repository: VectorRepository,
        embedding_service: EmbeddingService,
        conversation_service: ConversationService,
        collection_name: str,
        upload_folder: str
    ):
        """
        Initialize the service with dependencies.
        
        Args:
            vector_repository: Repository for vector storage and search
            embedding_service: Service for generating embeddings
            conversation_service: Service for conversation management
            collection_name: Name of the vector collection
            upload_folder: Path to the upload folder
        """
        self.vector_repository = vector_repository
        self.embedding_service = embedding_service
        self.conversation_service = conversation_service
        self.collection_name = collection_name
        self.upload_folder = upload_folder
        
        # Create upload directory if it doesn't exist
        os.makedirs(upload_folder, exist_ok=True)
    
    def process_document(
        self,
        file_path: str,
        filename: str,
        conversation_id: Optional[str] = None,
        clear_collection: bool = True
    ) -> DocumentUploadResponseDTO:
        """
        Process a document for indexing and RAG.
        
        Args:
            file_path: Path to the file
            filename: Original filename
            conversation_id: ID of the conversation to associate with (optional)
            clear_collection: Whether to clear the collection before indexing
            
        Returns:
            Response DTO with processing results
        """
        start_time = time.time()
        
        # Determine file type
        is_zip = filename.endswith(".zip")
        file_type = "zip" if is_zip else "file"
        
        # Process file based on type
        if is_zip:
            chunks = self._process_zip_file(file_path)
        else:
            chunks = self._process_single_file(file_path)
        
        # Clear collection if requested
        if clear_collection:
            self.vector_repository.clear_collection(self.collection_name)
        
        # Generate document chunks with embeddings
        document_chunks = []
        for chunk in chunks:
            # Generate embedding
            embedding = self.embedding_service.get_embedding(chunk.page_content)
            
            # Create document chunk with embedding
            document_chunk = DocumentChunk(
                content=chunk.page_content,
                metadata=chunk.metadata,
                embedding=embedding
            )
            
            document_chunks.append(document_chunk)
        
        # Add to vector repository
        self.vector_repository.add_documents(self.collection_name, document_chunks)
        
        # Create or get conversation
        if not conversation_id:
            conversation_dto = self.conversation_service.create_conversation(
                title=f"Project: {filename}",
                initial_message=f"I've indexed your project '{filename}' with code compression enabled. What would you like to know about it?"
            )
            conversation_id = conversation_dto.id
        
        # Create document ID
        document_id = str(uuid.uuid4())
        
        # Add document to conversation
        document_info = {
            "id": document_id,
            "filename": filename,
            "type": file_type,
            "compression_enabled": True,
            "chunk_count": len(chunks),
            "added_at": datetime.utcnow().isoformat(),
            "metadata": {
                "file_size": os.path.getsize(file_path) if os.path.exists(file_path) else 0,
                "chunk_count": len(chunks),
                "embedding_model": self._get_embedding_model_name()
            }
        }
        
        document_dto = self.conversation_service.add_document_to_conversation(
            conversation_id, 
            document_info
        )
        
        # Calculate processing time
        processing_time_ms = (time.time() - start_time) * 1000
        
        # Prepare success message
        if is_zip:
            message = "Project files indexed with code compression. You can now ask questions about your code with reduced token usage."
        else:
            message = "File indexed with code compression. You can now ask questions about it with reduced token usage."
        
        # Create and return response DTO
        return DocumentUploadResponseDTO(
            message=message,
            conversation_id=conversation_id,
            document_id=document_id,
            compression_enabled=True,
            chunks_processed=len(chunks),
            file_type=file_type,
            processing_time_ms=processing_time_ms
        )
    
    def get_document_by_id(self, document_id: str) -> Optional[DocumentDTO]:
        """
        Get a document by ID.
        
        Args:
            document_id: The document ID
            
        Returns:
            Document DTO if found, None otherwise
        """
        # This would typically query a document repository
        # For simplicity, we'll search through all conversations
        conversations = self.conversation_service.get_all_conversations()
        
        for conversation_item in conversations:
            conversation = self.conversation_service.get_conversation(conversation_item.id)
            if not conversation:
                continue
                
            for document in conversation.documents:
                if document.id == document_id:
                    return document
        
        return None
    
    def get_document_chunks(self, document_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get chunks belonging to a specific document.
        
        Args:
            document_id: The document ID
            limit: Maximum number of chunks to return
            
        Returns:
            List of document chunks
        """
        # This would typically create a query with a filter on document_id
        # For simplicity, we'll use a placeholder implementation
        # In a real implementation, you would modify vector_repository to support filtering
        
        # Create a generic query vector
        query = f"document_id:{document_id}"
        query_vector = self.embedding_service.get_embedding(query)
        
        # Search with the query vector
        results = self.vector_repository.search_similar(
            self.collection_name,
            query_vector,
            limit=limit
        )
        
        # Filter results to only include chunks from this document
        # This is a fallback since we don't have proper filtering in the repository
        filtered_results = []
        for result in results:
            metadata = result.get("metadata", {})
            if metadata.get("document_id") == document_id:
                filtered_results.append(result)
        
        return filtered_results
    
    def _process_single_file(self, file_path: str) -> List[Any]:
        """
        Process a single file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            List of document chunks
        """
        # This would typically use a document processor from the infrastructure layer
        # For brevity, we'll use langchain's document loaders directly
        from langchain_community.document_loaders import TextLoader
        from langchain.text_splitter import CharacterTextSplitter
        
        try:
            # Use text loader for all text-based files
            loader = TextLoader(file_path, encoding='utf-8')
            documents = loader.load()
            
            # Split into chunks
            text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
            chunks = text_splitter.split_documents(documents)
            
            # Add document_id to metadata (will be populated later)
            for chunk in chunks:
                if "metadata" not in chunk or not isinstance(chunk.metadata, dict):
                    chunk.metadata = {}
                
                # Add file information
                chunk.metadata["file_path"] = file_path
                chunk.metadata["file_name"] = os.path.basename(file_path)
            
            return chunks
        except Exception as e:
            # Handle errors appropriately
            print(f"Error processing file {file_path}: {str(e)}")
            # Return a single chunk with error information
            from langchain.docstore.document import Document
            return [Document(
                page_content=f"Error processing file: {str(e)}",
                metadata={"file_path": file_path, "error": True}
            )]
    
    def _process_zip_file(self, zip_path: str) -> List[Any]:
        """
        Process a ZIP file by extracting and processing its contents.
        
        Args:
            zip_path: Path to the ZIP file
            
        Returns:
            List of document chunks
        """
        chunks = []
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Extract the zip file
            try:
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(temp_dir)
            except Exception as e:
                print(f"Error extracting ZIP file {zip_path}: {str(e)}")
                return chunks
            
            # Process each file in the extracted directory
            for root, _, files in os.walk(temp_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    # Skip binary and specific file types
                    if self._should_process_file(file_path):
                        file_chunks = self._process_single_file(file_path)
                        chunks.extend(file_chunks)
        
        return chunks
    
    def _should_process_file(self, file_path: str) -> bool:
        """
        Determine if a file should be processed.
        
        Args:
            file_path: Path to the file
            
        Returns:
            True if the file should be processed, False otherwise
        """
        # Skip binary files and other files we don't want to process
        _, file_extension = os.path.splitext(file_path)
        
        # List of extensions to skip
        skip_extensions = [
            '.pyc', '.exe', '.dll', '.so', '.bin', '.dat', '.db',
            '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.ico', '.svg',
            '.mp3', '.mp4', '.avi', '.mov', '.wav', '.flac',
            '.zip', '.tar', '.gz', '.rar', '.7z'
        ]
        
        # Check if the file extension is in the skip list
        if file_extension.lower() in skip_extensions:
            return False
        
        # Check if it's a common binary file pattern
        binary_patterns = ['.git/', '__pycache__/', 'node_modules/']
        for pattern in binary_patterns:
            if pattern in file_path:
                return False
        
        return True
    
    def _get_embedding_model_name(self) -> str:
        """
        Get the name of the embedding model being used.
        
        Returns:
            Name of the embedding model
        """
        # This is a placeholder implementation
        # In a real implementation, this would get the model name from the embedding service
        return "sentence-transformer"