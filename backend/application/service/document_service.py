import os
import uuid
import tempfile
import zipfile
import time
from typing import List, Dict, Any, Optional
from datetime import datetime

from langchain.docstore.document import Document
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader, TextLoader
import mammoth

from backend.domain.port.repository.vector_repository import VectorRepository
from backend.domain.port.service.embedding_service import EmbeddingService
from backend.domain.port.service.document_processor_service import DocumentProcessorService
from backend.domain.model.document_chunk import DocumentChunk
from backend.application.service.conversation_service import ConversationService
from backend.application.dto.query_dto import DocumentUploadRequestDTO, DocumentUploadResponseDTO
from backend.application.dto.conversation_dto import DocumentDTO


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
        document_processor: DocumentProcessorService
    ):
        """
        Initialize the service with dependencies.

        Args:
            vector_repository: Repository for vector storage and search
            embedding_service: Service for generating embeddings
            conversation_service: Service for conversation management
            document_processor: Service for processing documents
        """
        self.vector_repository = vector_repository
        self.embedding_service = embedding_service
        self.conversation_service = conversation_service
        self.document_processor = document_processor
        
        # Create upload directory if it doesn't exist
        os.makedirs(self.document_processor.upload_folder, exist_ok=True)

    def upload_document(self, upload_request: DocumentUploadRequestDTO) -> DocumentUploadResponseDTO:
        """
        Process a document upload request.
        
        Args:
            upload_request: DTO with upload information
            
        Returns:
            Response DTO with processing results
        """
        start_time = time.time()
        
        # File path is already provided in upload_request.file_path
        file_path = upload_request.file_path
        
        # Determine file type
        is_zip = upload_request.filename.endswith(".zip")
        file_type = "zip" if is_zip else "file"
        
        # Process the document
        if is_zip:
            chunks = self._process_zip_file(file_path)
        else:
            chunks = self._process_single_file(file_path)
        
        # Create document ID
        document_id = str(uuid.uuid4())
        
        # Generate document chunks with embeddings
        document_chunks = []
        for chunk in chunks:
            # Generate embedding
            embedding = self.embedding_service.get_embedding(chunk.page_content)
            
            # Create document chunk with embedding
            document_chunk = DocumentChunk(
                content=chunk.page_content,
                metadata=chunk.metadata,
                document_id=document_id,
                embedding=embedding
            )
            
            document_chunks.append(document_chunk)
        
        # Add to vector repository - note we don't pass collection_name anymore
        self.vector_repository.add_documents(document_chunks)
        
        # Create or get conversation
        if not upload_request.conversation_id:
            conversation_dto = self.conversation_service.create_conversation(
                title=f"Project: {upload_request.filename}",
                initial_message=f"I've indexed your file '{upload_request.filename}'. What would you like to know about it?"
            )
            conversation_id = conversation_dto.id
        else:
            conversation_id = upload_request.conversation_id
        
        # Add document to conversation
        document_info = {
            "id": document_id,
            "filename": upload_request.filename,
            "type": file_type,
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
            message = f"Project '{upload_request.filename}' with {len(chunks)} chunks has been indexed successfully."
        else:
            message = f"File '{upload_request.filename}' with {len(chunks)} chunks has been indexed successfully."
        
        # Create and return response DTO
        return DocumentUploadResponseDTO(
            message=message,
            conversation_id=conversation_id,
            document_id=document_id,
            compression_enabled=upload_request.compression_enabled,
            chunks_processed=len(chunks),
            file_type=file_type,
            processing_time_ms=processing_time_ms
        )

    def _process_single_file(self, file_path: str) -> List[Document]:
        """
        Process a single file using the appropriate document processor.

        Args:
            file_path: Path to the file

        Returns:
            List of document chunks
        """
        file_extension = os.path.splitext(file_path)[1].lower()

        try:
            if file_extension == ".pdf":
                # Use PyPDFLoader for PDF files
                loader = PyPDFLoader(file_path)
            elif file_extension == ".docx":
                # Use Docx2txtLoader for DOCX files
                loader = Docx2txtLoader(file_path)
            elif file_extension == ".doc":
                # Use mammoth for DOC files
                with open(file_path, "rb") as file:
                    result = mammoth.convert_to_html(file)
                    html = result.value
                    return [Document(page_content=html, metadata={"file_path": file_path, "file_name": os.path.basename(file_path)})]
            else:
                # Fallback to TextLoader for other text-based files
                loader = TextLoader(file_path, encoding="utf-8")

            # Load and split documents
            documents = loader.load()
            text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
            chunks = text_splitter.split_documents(documents)

            # Add file metadata to each chunk
            for chunk in chunks:
                if "metadata" not in chunk or not isinstance(chunk.metadata, dict):
                    chunk.metadata = {}
                chunk.metadata["file_path"] = file_path
                chunk.metadata["file_name"] = os.path.basename(file_path)

            return chunks
        except Exception as e:
            print(f"Error processing file {file_path}: {str(e)}")
            return [Document(page_content=f"Error processing file: {str(e)}", metadata={"file_path": file_path, "error": True})]

    def _process_zip_file(self, zip_path: str) -> List[Document]:
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
                with zipfile.ZipFile(zip_path, "r") as zip_ref:
                    zip_ref.extractall(temp_dir)
            except Exception as e:
                print(f"Error extracting ZIP file {zip_path}: {str(e)}")
                return chunks

            # Process each file in the extracted directory
            for root, _, files in os.walk(temp_dir):
                for file in files:
                    file_path = os.path.join(root, file)
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
        # Correctly unpack the result of os.path.splitext
        _, file_extension = os.path.splitext(file_path)
        file_extension = file_extension.lower()  # Ensure the extension is lowercase

        # Skip binary and unsupported files
        skip_extensions = [
            ".pyc", ".exe", ".dll", ".so", ".bin", ".dat", ".db",
            ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".ico", ".svg",
            ".mp3", ".mp4", ".avi", ".mov", ".wav", ".flac",
            ".zip", ".tar", ".gz", ".rar", ".7z"
        ]

        if file_extension in skip_extensions:
            return False

        # Skip common binary file patterns
        binary_patterns = [".git/", "__pycache__/", "node_modules/"]
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
        return "sentence-transformer"
