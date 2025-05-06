# src/infrastructure/service/document_processor.py
import os
import io
import zipfile
import tempfile
from typing import List, Dict, Any, Union
from pathlib import Path
import shutil

from src.domain.port.service.document_processor_service import DocumentProcessorService
from src.domain.model.document import Document
from src.domain.model.document_chunk import DocumentChunk

class DocumentProcessor(DocumentProcessorService):
    """
    Implementation of the DocumentProcessorService interface.
    Handles loading, processing and chunking various document types.
    """
    
    def __init__(self, upload_folder: str):
        """
        Initialize the document processor.
        
        Args:
            upload_folder: Path to temporary upload folder
        """
        self.upload_folder = upload_folder
        os.makedirs(upload_folder, exist_ok=True)
    
    def process_file(self, file_path: Union[str, Path], file_name: str, metadata: Dict[str, Any] = None) -> Document:
        """
        Process a file from disk and extract its content.
        
        Args:
            file_path: Path to the file
            file_name: Name of the file
            metadata: Additional metadata for the document
            
        Returns:
            A Document object with the processed content
        """
        file_path = str(file_path)  # Ensure string path
        
        # Default metadata
        if metadata is None:
            metadata = {}
        
        # Determine file type
        file_ext = os.path.splitext(file_name)[1].lower()
        
        # Process based on file type
        if file_ext == '.zip':
            return self._process_zip_file(file_path, file_name, metadata)
        elif file_ext in ['.py', '.js', '.ts', '.java', '.c', '.cpp', '.h', '.cs', '.html', '.css', '.md', '.txt']:
            return self._process_text_file(file_path, file_name, metadata)
        else:
            # For unsupported types, just store as plain text
            return self._process_generic_file(file_path, file_name, metadata)
    
    def process_binary(self, binary_data: Union[bytes, io.BytesIO], file_name: str, metadata: Dict[str, Any] = None) -> Document:
        """
        Process binary data and return a Document.
        
        Args:
            binary_data: Binary content of the file
            file_name: Name of the file
            metadata: Additional metadata for the document
            
        Returns:
            A Document object with the processed content
        """
        # Save to temporary file first
        if isinstance(binary_data, io.BytesIO):
            binary_data = binary_data.getvalue()
        
        temp_file_path = os.path.join(self.upload_folder, file_name)
        
        try:
            with open(temp_file_path, 'wb') as f:
                f.write(binary_data)
            
            # Process the file
            document = self.process_file(temp_file_path, file_name, metadata)
            
            return document
        finally:
            # Clean up the temporary file
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
    
    def chunk_document(self, document: Document, chunk_size: int = 1000, chunk_overlap: int = 200) -> List[DocumentChunk]:
        """
        Split a document into chunks for efficient processing and retrieval.
        
        Args:
            document: The document to chunk
            chunk_size: Maximum size of each chunk in characters
            chunk_overlap: Overlap between consecutive chunks in characters
            
        Returns:
            List of DocumentChunk objects
        """
        chunks = []
        content = document.content
        
        # Skip chunking for very short documents
        if len(content) <= chunk_size:
            chunk = DocumentChunk(
                content=content,
                metadata=document.metadata.copy(),
                document_id=document.id
            )
            chunks.append(chunk)
            return chunks
        
        # Chunk by splitting on newlines when possible
        start = 0
        while start < len(content):
            end = start + chunk_size
            
            if end >= len(content):
                # Last chunk
                chunk_text = content[start:]
            else:
                # Try to find a newline to break on
                newline_pos = content.rfind('\n', start, end)
                if newline_pos > start:
                    end = newline_pos + 1  # Include the newline
                
                chunk_text = content[start:end]
            
            # Create chunk with metadata
            chunk_metadata = document.metadata.copy()
            chunk_metadata["chunk_index"] = len(chunks)
            chunk_metadata["char_start"] = start
            chunk_metadata["char_end"] = end
            
            chunk = DocumentChunk(
                content=chunk_text,
                metadata=chunk_metadata,
                document_id=document.id
            )
            chunks.append(chunk)
            
            # Move start position for the next chunk, considering overlap
            start = max(start, end - chunk_overlap)
        
        return chunks
    
    def get_supported_file_types(self) -> List[str]:
        """
        Get a list of supported file extensions.
        
        Returns:
            List of supported file extensions
        """
        return [
            '.py', '.js', '.ts', '.java', '.c', '.cpp', '.h', '.cs',
            '.html', '.css', '.md', '.txt', '.json', '.xml', '.zip'
        ]
    
    # Private helper methods
    
    def _process_text_file(self, file_path: str, file_name: str, metadata: Dict[str, Any]) -> Document:
        """Process a text file."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
            
            # Update metadata
            metadata.update({
                "file_type": "text",
                "filename": file_name,
                "extension": os.path.splitext(file_name)[1].lower()
            })
            
            # Create document
            return Document(
                filename=file_name,
                content=content,
                type="file",
                metadata=metadata
            )
        except Exception as e:
            # Log error and return empty document
            print(f"Error processing text file {file_name}: {e}")
            return Document(
                filename=file_name,
                content=f"Error processing file: {str(e)}",
                type="file",
                metadata=metadata
            )
    
    def _process_zip_file(self, file_path: str, file_name: str, metadata: Dict[str, Any]) -> Document:
        """Process a ZIP archive."""
        temp_dir = tempfile.mkdtemp(dir=self.upload_folder)
        
        try:
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
            
            # Collect text from all supported files
            all_text = []
            file_count = 0
            supported_exts = set(self.get_supported_file_types())
            
            for root, _, files in os.walk(temp_dir):
                for file in files:
                    ext = os.path.splitext(file)[1].lower()
                    if ext in supported_exts and ext != '.zip':  # Avoid nested ZIPs
                        file_path = os.path.join(root, file)
                        rel_path = os.path.relpath(file_path, temp_dir)
                        
                        try:
                            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                                file_content = f.read()
                                
                            # Add file header and content
                            all_text.append(f"\n\n--- File: {rel_path} ---\n\n")
                            all_text.append(file_content)
                            file_count += 1
                        except Exception as e:
                            all_text.append(f"\n\n--- File: {rel_path} (Error: {str(e)}) ---\n\n")
            
            # Update metadata
            metadata.update({
                "file_type": "zip",
                "filename": file_name,
                "file_count": file_count
            })
            
            # Create document
            return Document(
                filename=file_name,
                content=''.join(all_text),
                type="zip",
                metadata=metadata
            )
        except Exception as e:
            # Log error and return empty document
            print(f"Error processing ZIP file {file_name}: {e}")
            return Document(
                filename=file_name,
                content=f"Error processing ZIP file: {str(e)}",
                type="zip",
                metadata=metadata
            )
        finally:
            # Clean up temp directory
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    def _process_generic_file(self, file_path: str, file_name: str, metadata: Dict[str, Any]) -> Document:
        """Process a generic file as text."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
        except:
            # If can't read as text, use placeholder
            content = f"[Binary file: {file_name}]"
        
        # Update metadata
        metadata.update({
            "file_type": "generic",
            "filename": file_name,
            "extension": os.path.splitext(file_name)[1].lower()
        })
        
        # Create document
        return Document(
            filename=file_name,
            content=content,
            type="file",
            metadata=metadata
        ) 