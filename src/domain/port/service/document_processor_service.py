from abc import ABC, abstractmethod
from typing import List, Dict, Any, Union
from pathlib import Path
import io

from src.domain.model.document import Document
from src.domain.model.document_chunk import DocumentChunk

class DocumentProcessorService(ABC):
    """
    Port (interface) for document processing services.
    This interface defines operations for loading, chunking, and processing documents.
    
    Implementations might handle different document types or use different chunking strategies.
    """
    
    @abstractmethod
    def process_file(self, file_path: Union[str, Path], file_name: str, metadata: Dict[str, Any] = None) -> Document:
        """
        Process a file and return a Document with extracted text and metadata.
        
        Args:
            file_path: Path to the file
            file_name: Name of the file
            metadata: Additional metadata for the document
            
        Returns:
            A Document object with the processed content
        """
        pass
    
    @abstractmethod
    def process_binary(self, binary_data: Union[bytes, io.BytesIO], file_name: str, metadata: Dict[str, Any] = None) -> Document:
        """
        Process binary data and return a Document with extracted text and metadata.
        
        Args:
            binary_data: Binary content of the file
            file_name: Name of the file
            metadata: Additional metadata for the document
            
        Returns:
            A Document object with the processed content
        """
        pass
    
    @abstractmethod
    def chunk_document(self, document: Document, chunk_size: int = 1000, chunk_overlap: int = 200) -> List[DocumentChunk]:
        """
        Split a document into chunks for efficient processing and retrieval.
        
        Args:
            document: The document to chunk
            chunk_size: Maximum size of each chunk
            chunk_overlap: Overlap between consecutive chunks
            
        Returns:
            List of DocumentChunk objects
        """
        pass
    
    @abstractmethod
    def get_supported_file_types(self) -> List[str]:
        """
        Get a list of supported file extensions.
        
        Returns:
            List of supported file extensions
        """
        pass 