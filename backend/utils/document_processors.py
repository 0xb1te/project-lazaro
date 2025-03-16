import os
import tempfile
from langchain.docstore.document import Document
from langchain.text_splitter import CharacterTextSplitter

# For PDF processing
from langchain_community.document_loaders import PyPDFLoader

# For DOCX processing
from langchain_community.document_loaders import Docx2txtLoader

# For DOC processing (using mammoth as a fallback)
import mammoth
import io

def process_pdf_document(file_path):
    """
    Process a PDF file using PyPDFLoader.
    
    Args:
        file_path (str): Path to the PDF file
        
    Returns:
        list: List of document chunks
    """
    try:
        # Use PyPDFLoader to load the PDF
        loader = PyPDFLoader(file_path)
        documents = loader.load()
        
        # Split the document into chunks
        text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        texts = text_splitter.split_documents(documents)
        
        print(f"Successfully processed PDF: {file_path} - Extracted {len(texts)} chunks")
        return texts
    except Exception as e:
        print(f"Error processing PDF file {file_path}: {str(e)}")
        # Return empty list on error
        return []

def process_docx_document(file_path):
    """
    Process a DOCX file using Docx2txtLoader.
    
    Args:
        file_path (str): Path to the DOCX file
        
    Returns:
        list: List of document chunks
    """
    try:
        # Use Docx2txtLoader to load the DOCX
        loader = Docx2txtLoader(file_path)
        documents = loader.load()
        
        # Split the document into chunks
        text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        texts = text_splitter.split_documents(documents)
        
        print(f"Successfully processed DOCX: {file_path} - Extracted {len(texts)} chunks")
        return texts
    except Exception as e:
        print(f"Error processing DOCX file {file_path}: {str(e)}")
        # Return empty list on error
        return []

def process_doc_document(file_path):
    """
    Process a DOC file using mammoth.
    
    Args:
        file_path (str): Path to the DOC file
        
    Returns:
        list: List of document chunks
    """
    try:
        # Read the file
        with open(file_path, 'rb') as file:
            # Convert to HTML using mammoth
            result = mammoth.convert_to_html(file)
            html = result.value
            
            # Create a Document object
            document = Document(
                page_content=html,
                metadata={
                    "file_path": file_path,
                    "file_name": os.path.basename(file_path),
                    "format": "doc"
                }
            )
            
            # Split the document into chunks
            text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
            texts = text_splitter.split_documents([document])
            
            print(f"Successfully processed DOC: {file_path} - Extracted {len(texts)} chunks")
            return texts
    except Exception as e:
        print(f"Error processing DOC file {file_path}: {str(e)}")
        # Return empty list on error
        return []

def get_document_extensions():
    """
    Returns a list of all supported document extensions.
    
    Returns:
        list: List of supported document extensions
    """
    return ['.pdf', '.docx', '.doc']

def get_document_processor(file_path):
    """
    Returns the appropriate document processor based on file extension.
    
    Args:
        file_path (str): Path to the document file
        
    Returns:
        function: The appropriate processing function
    """
    # Get the lowercase file extension
    file_extension = os.path.splitext(file_path)[1].lower()
    
    # Return the appropriate processor
    if file_extension == '.pdf':
        return process_pdf_document
    elif file_extension == '.docx':
        return process_docx_document
    elif file_extension == '.doc':
        return process_doc_document
    else:
        return None

def is_document_file(file_path):
    """
    Checks if a file is a supported document type.
    
    Args:
        file_path (str): Path to the file
        
    Returns:
        bool: True if the file is a supported document type
    """
    file_extension = os.path.splitext(file_path)[1].lower()
    return file_extension in get_document_extensions()