import os
import uuid
import tempfile
import zipfile
import time
import json
import logging
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
from backend.application.dto.document_dto import (
    DocumentUploadRequestDTO,
    DocumentUploadResponseDTO,
    DocumentDTO,
    DocumentChunkDTO
)
from backend.application.dto.conversation_dto import DocumentDTO
from backend.application.dto.file_analysis_dto import FileAnalysisRequestDTO
from backend.application.service.file_analysis_service import FileAnalysisService

class DocumentProcessingError(Exception):
    """Exception raised for errors during document processing."""
    pass

# Configure logger
logger = logging.getLogger(__name__)

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
        document_processor: DocumentProcessorService,
        file_analysis_service: FileAnalysisService
    ):
        """
        Initialize the service with dependencies.

        Args:
            vector_repository: Repository for vector storage and search
            embedding_service: Service for generating embeddings
            conversation_service: Service for conversation management
            document_processor: Service for processing documents
            file_analysis_service: Service for file analysis
        """
        self.vector_repository = vector_repository
        self.embedding_service = embedding_service
        self.conversation_service = conversation_service
        self.document_processor = document_processor
        self.file_analysis_service = file_analysis_service
        
        # Create upload directory if it doesn't exist
        os.makedirs(self.document_processor.upload_folder, exist_ok=True)

    def upload_document(self, upload_request: DocumentUploadRequestDTO) -> DocumentUploadResponseDTO:
        """
        Upload and process a document.
        
        Args:
            upload_request: The upload request containing the file and metadata
            
        Returns:
            DocumentUploadResponseDTO with the processing results
        """
        try:
            start_time = time.time()
            file_extension = os.path.splitext(upload_request.file_path)[1].lower()
            
            # Handle zip files
            if file_extension == '.zip':
                chunks = self._process_zip_file(upload_request.file_path, upload_request.conversation_id)
                if not chunks:
                    raise DocumentProcessingError("No processable content found in zip file")
                    
                # Create conversation if it doesn't exist
                if not upload_request.conversation_id:
                    conversation = self.conversation_service.create_conversation(
                        title=f"Analysis of {os.path.basename(upload_request.file_path)}"
                    )
                    upload_request.conversation_id = conversation.id
                
                # Generate embeddings for chunks
                processed_chunks = []
                for chunk in chunks:
                    try:
                        # Skip embedding generation for analysis documents
                        if chunk.metadata.get('type') == 'analysis':
                            processed_chunks.append(chunk)
                            continue
                            
                        # Generate embedding
                        embedding = self.embedding_service.get_embedding(chunk.page_content)
                        # Store embedding in metadata since Document class doesn't support direct embedding
                        chunk.metadata['embedding'] = embedding
                        processed_chunks.append(chunk)
                        logger.debug(f"Generated embedding for chunk from file: {chunk.metadata.get('filename')}")
                    except Exception as e:
                        logger.warning(f"Failed to generate embedding for chunk from file {chunk.metadata.get('filename')}: {str(e)}")
                        continue
                
                if not processed_chunks:
                    raise DocumentProcessingError("Failed to process any chunks with embeddings")
                
                logger.info(f"Successfully processed {len(processed_chunks)} chunks with embeddings")
                
                # Convert chunks to DocumentChunk objects for vector store
                vector_chunks = []
                document_id = str(uuid.uuid4())  # Generate one document ID for all chunks from the same file
                
                for chunk in processed_chunks:
                    if chunk.metadata.get('type') == 'analysis':
                        # For analysis documents, create a special chunk
                        vector_chunk = DocumentChunk(
                            content=chunk.page_content,
                            metadata={
                                **chunk.metadata,
                                'conversation_id': upload_request.conversation_id
                            },
                            document_id=document_id
                        )
                    else:
                        # For regular content chunks
                        vector_chunk = DocumentChunk(
                            content=chunk.page_content,
                            metadata={
                                **chunk.metadata,
                                'conversation_id': upload_request.conversation_id
                            },
                            document_id=document_id,
                            embedding=chunk.metadata.pop('embedding')  # Remove embedding from metadata after using it
                        )
                    vector_chunks.append(vector_chunk)
                
                # Add chunks to vector store
                self.vector_repository.add_documents(vector_chunks, upload_request.conversation_id)
                
                processing_time = (time.time() - start_time) * 1000  # Convert to milliseconds
                
                return DocumentUploadResponseDTO(
                    message=f"ZIP file processed successfully. Processed {len(vector_chunks)} chunks.",
                    conversation_id=upload_request.conversation_id,
                    document_id=document_id,
                    compression_enabled=True,
                    chunks_processed=len(vector_chunks),
                    file_type=file_extension,
                    processing_time_ms=processing_time
                )
            
            raise DocumentProcessingError("Only ZIP files are supported")

        except Exception as e:
            logger.error(f"Error processing document: {str(e)}")
            if isinstance(e, DocumentProcessingError):
                raise e
            raise DocumentProcessingError(f"Error uploading document: {str(e)}")

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
                # For text-based files, try to read with different encodings
                with open(file_path, 'rb') as f:
                    binary_content = f.read()
                
                # Try different encodings
                encodings = ['utf-8', 'latin1', 'cp1252', 'iso-8859-1']
                content = None
                
                for encoding in encodings:
                    try:
                        content = binary_content.decode(encoding)
                        break
                    except UnicodeDecodeError:
                        continue
                
                if content is None:
                    content = binary_content.decode('utf-8', errors='ignore')
                
                return [Document(page_content=content, metadata={"file_path": file_path, "file_name": os.path.basename(file_path)})]

            # Load and split documents for loaders
            if 'loader' in locals():
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
            
            return []

        except Exception as e:
            logger.error(f"Error processing file {file_path}: {str(e)}")
            return [Document(page_content=f"Error processing file: {str(e)}", metadata={"file_path": file_path, "error": True})]

    def _process_zip_file(self, zip_path: str, conversation_id: str) -> List[Document]:
        """
        Process a ZIP file by extracting and processing its contents.
        Uses only built-in Python libraries.

        Args:
            zip_path: Path to the ZIP file
            conversation_id: ID of the conversation

        Returns:
            List of document chunks
        """
        chunks = []
        processed_files = 0
        skipped_files = 0
        
        # Store all file contents first to analyze relationships
        file_contents = {}
        file_analyses = {}
        
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                # First, check if the zip file is not too large
                total_size = sum(info.file_size for info in zip_ref.filelist)
                if total_size > 100 * 1024 * 1024:  # 100MB limit
                    raise DocumentProcessingError("ZIP file is too large (max 100MB)")
                
                # First pass: collect all valid files and their contents
                for file_info in zip_ref.filelist:
                    # Skip directories and unwanted paths
                    if (file_info.filename.endswith('/') or
                        any(pattern in file_info.filename for pattern in [
                            '__pycache__/', '.git/', 'node_modules/', 
                            'venv/', '.env/', 'build/', 'dist/',
                            'bin/', 'obj/'
                        ])):
                        continue
                    
                    # Get file extension
                    _, ext = os.path.splitext(file_info.filename)
                    ext = ext.lower()
                    
                    # Process only supported file types
                    if ext in [
                        '.txt', '.py', '.js', '.html', '.css', '.json', '.md',
                        '.xml', '.yaml', '.yml', '.ini', '.conf', '.cfg',
                        '.ipynb', '.sh', '.bat', '.sql', '.csv', '.tsv',
                        '.log', '.rst', '.tex'
                    ]:
                        try:
                            # Read file content
                            with zip_ref.open(file_info.filename) as file:
                                binary_content = file.read()
                                
                                # Try different encodings
                                content = None
                                for encoding in ['utf-8', 'latin1', 'cp1252', 'iso-8859-1']:
                                    try:
                                        content = binary_content.decode(encoding)
                                        break
                                    except UnicodeDecodeError:
                                        continue
                                
                                if content is None:
                                    content = binary_content.decode('utf-8', errors='ignore')
                                
                                file_contents[file_info.filename] = {
                                    'content': content,
                                    'type': ext,
                                    'size': file_info.file_size
                                }
                                processed_files += 1
                        except Exception as e:
                            logger.warning(f"Error reading file {file_info.filename}: {str(e)}")
                            skipped_files += 1
                            continue
                    else:
                        skipped_files += 1
                        logger.debug(f"Skipping unsupported file type: {file_info.filename}")
                
                # Second pass: analyze files and their relationships
                for filename, file_data in file_contents.items():
                    try:
                        # Analyze each file
                        analysis = self.file_analysis_service.analyze_file(
                            FileAnalysisRequestDTO(
                                file_path=filename,
                                content=file_data['content']
                            )
                        )
                        file_analyses[filename] = analysis
                        
                        # Create analysis document
                        analysis_id = str(uuid.uuid4())
                        analysis_doc = Document(
                            page_content=json.dumps(analysis.to_dict()),
                            metadata={
                                "type": "analysis",
                                "original_file": filename,
                                "file_type": file_data['type'],
                                "compressed": True,
                                "conversation_id": conversation_id,
                                "id": analysis_id,
                                "filename": f"analysis_{filename}"
                            }
                        )
                        chunks.append(analysis_doc)
                        
                        # Create content chunks
                        text_splitter = CharacterTextSplitter(
                            chunk_size=1000,
                            chunk_overlap=200,
                            separator="\n"
                        )
                        
                        texts = text_splitter.split_text(file_data['content'])
                        
                        for i, text in enumerate(texts):
                            chunk = Document(
                                page_content=text,
                                metadata={
                                    "source": zip_path,
                                    "filename": filename,
                                    "chunk": i,
                                    "total_chunks": len(texts),
                                    "file_type": file_data['type'],
                                    "compressed": True,
                                    "file_size": file_data['size'],
                                    "analysis_id": analysis_id,
                                    "conversation_id": conversation_id
                                }
                            )
                            chunks.append(chunk)
                    except Exception as e:
                        logger.warning(f"Error analyzing file {filename}: {str(e)}")
                        continue
                
                # Generate and add index document
                if file_analyses:
                    try:
                        # Get project name from the zip file or first directory
                        project_name = os.path.splitext(os.path.basename(zip_path))[0]
                        
                        # Generate index content
                        index_content = self.file_analysis_service.create_index_document(list(file_analyses.values()))
                        
                        # Save index to conversation storage
                        storage_dir = os.path.join(self.document_processor.storage_dir, "conversations", conversation_id)
                        os.makedirs(storage_dir, exist_ok=True)
                        index_path = os.path.join(storage_dir, "index.md")
                        
                        with open(index_path, 'w', encoding='utf-8') as f:
                            f.write(index_content)
                        
                        # Create specialized text splitter for index document
                        index_splitter = CharacterTextSplitter(
                            chunk_size=500,  # Smaller chunks for index
                            chunk_overlap=200,  # 40% overlap
                            separator="\n## ",  # Preserve section boundaries
                            keep_separator=True
                        )
                        
                        # Split index content into chunks
                        index_chunks = index_splitter.split_text(index_content)
                        
                        # Get all filenames that were analyzed
                        indexed_files = [analysis.file_path for analysis in file_analyses.values()]
                        
                        # Create index document chunks
                        index_doc_chunks = []
                        for i, chunk in enumerate(index_chunks):
                            # Determine section type based on content
                            section_type = "overview"
                            if "# File Catalog" in chunk:
                                section_type = "catalog"
                            elif "# Dependency Map" in chunk or "# Architecture Overview" in chunk:
                                section_type = "dependency"
                            elif "# File Summaries" in chunk:
                                section_type = "file_summary"
                            
                            # Get relevant files for this chunk
                            chunk_files = [f for f in indexed_files if f in chunk]
                            
                            # Create document chunk with enhanced metadata
                            chunk_doc = Document(
                                page_content=chunk,
                                metadata={
                                    "document_type": "index",
                                    "is_index": True,
                                    "indexed_files": indexed_files,
                                    "project_name": project_name,
                                    "creation_timestamp": datetime.utcnow().isoformat(),
                                    "file_count": len(indexed_files),
                                    "retrieval_priority": "high",
                                    "section_type": section_type,
                                    "chunk_files": chunk_files,
                                    "chunk_number": i,
                                    "total_chunks": len(index_chunks),
                                    "conversation_id": conversation_id,
                                    "source": index_path,
                                    "filename": "index.md"
                                }
                            )
                            index_doc_chunks.append(chunk_doc)
                        
                        # Add index chunks to the list of all chunks
                        chunks.extend(index_doc_chunks)
                        logger.info(f"Created index document with {len(index_doc_chunks)} chunks")
                        
                    except Exception as e:
                        logger.warning(f"Error generating index document: {str(e)}")
                        raise
        
        except Exception as e:
            logger.error(f"Error processing zip file: {str(e)}")
            raise DocumentProcessingError(f"Error processing zip file: {str(e)}")
        
        logger.info(f"ZIP processing complete: {processed_files} files processed, {skipped_files} files skipped, {len(chunks)} total chunks created")
        return chunks

    def _should_process_file(self, file_path: str) -> bool:
        """
        Determine if a file should be processed.

        Args:
            file_path: Path to the file

        Returns:
            True if the file should be processed, False otherwise
        """
        _, file_extension = os.path.splitext(file_path)
        file_extension = file_extension.lower()

        # Only allow zip files
        if file_extension != '.zip':
            logger.warning(f"Skipping non-zip file: {file_path}")
            return False

        return True
    
    def _get_embedding_model_name(self) -> str:
        """
        Get the name of the embedding model being used.

        Returns:
            Name of the embedding model
        """
        return "sentence-transformer"

    def _create_document_chunks(self, document: Dict[str, Any]) -> List[Document]:
        """
        Create document chunks from a given document.

        Args:
            document: Dictionary representing the document

        Returns:
            List of document chunks
        """
        chunks = self._process_single_file(document["file_path"])
        for chunk in chunks:
            chunk.metadata["id"] = document["id"]
            chunk.metadata["filename"] = document["filename"]
            chunk.metadata["type"] = document["metadata"]["type"]
            chunk.metadata["conversation_id"] = document["metadata"]["conversation_id"]
        return chunks

    def _process_content(self, content: str, file_path: str) -> List[Document]:
        """
        Process content into document chunks.
        
        Args:
            content: The text content to process
            file_path: Path to the original file
            
        Returns:
            List of document chunks
        """
        # Create text splitter
        text_splitter = CharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separator="\n"
        )
        
        # Split text into chunks
        texts = text_splitter.split_text(content)
        
        # Create documents from chunks
        chunks = []
        for i, text in enumerate(texts):
            chunk = Document(
                page_content=text,
                metadata={
                    "source": file_path,
                    "chunk": i,
                    "filename": os.path.basename(file_path)
                }
            )
            chunks.append(chunk)
        
        return chunks

    def process_document(self, file_path: str, file_name: str, metadata: Dict[str, Any] = None) -> Document:
        """
        Process a document and store it in the vector database.
        
        Args:
            file_path: Path to the file
            file_name: Name of the file
            metadata: Additional metadata for the document
            
        Returns:
            The processed Document
        """
        try:
            start_time = time.time()
            
            # Process the file
            document = self.document_processor.process_file(file_path, file_name, metadata)
            
            # Generate embeddings for the document
            document_embedding = self.embedding_service.generate_embedding(document.content)
            
            # Store in vector database
            self.vector_repository.store_document(document, document_embedding)
            
            # Log processing time
            processing_time = time.time() - start_time
            print(f"Document processed in {processing_time:.2f} seconds")
            
            return document
            
        except Exception as e:
            print(f"Error processing document: {str(e)}")
            raise
