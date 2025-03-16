import zipfile
import tempfile
import os
from langchain_community.document_loaders import TextLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain.docstore.document import Document

# Import the document processors
from .document_processors import (
    process_pdf_document,
    process_docx_document,
    process_doc_document,
    get_document_processor,
    is_document_file,
    get_document_extensions
)

def process_file(file_path):
    """
    Process a single file based on its extension.
    
    Args:
        file_path (str): Path to the file
        
    Returns:
        list: List of document chunks
    """
    # Check if the file is a document file
    if is_document_file(file_path):
        processor = get_document_processor(file_path)
        if processor:
            return processor(file_path)
    
    # Default to TextLoader for text files
    try:
        loader = TextLoader(file_path)
        documents = loader.load()
        text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        texts = text_splitter.split_documents(documents)
        return texts
    except UnicodeDecodeError:
        print(f"File {file_path} is not a text file or has unsupported encoding")
        return []
    except Exception as e:
        print(f"Error processing file {file_path}: {str(e)}")
        return []

def process_zip_file(zip_path):
    """
    Process a ZIP file by extracting and processing its contents.
    
    Args:
        zip_path (str): Path to the ZIP file
        
    Returns:
        list: List of document chunks from all files
    """
    texts = []
    processed_files_count = 0
    document_files_count = 0
    
    # Get supported document extensions
    document_extensions = get_document_extensions()
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Extract the zip file
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
                print(f"Extracted ZIP file to {temp_dir}")
        except Exception as e:
            print(f"Error extracting ZIP file {zip_path}: {str(e)}")
            return texts
        
        # Walk through the extracted directory
        for root, _, files in os.walk(temp_dir):
            for file in files:
                file_path = os.path.join(root, file)
                file_extension = os.path.splitext(file)[1].lower()
                
                try:
                    # Skip known binary files
                    if file.endswith((".pyc", ".git", ".bin", ".exe", ".dll", ".so")):
                        print(f"Skipping binary file: {file_path}")
                        continue
                    
                    # Process document files (PDF, DOCX, DOC)
                    if file_extension in document_extensions:
                        document_files_count += 1
                        print(f"Found document file: {file_path}")
                        processor = get_document_processor(file_path)
                        
                        if processor:
                            try:
                                file_texts = processor(file_path)
                                if file_texts and len(file_texts) > 0:
                                    texts.extend(file_texts)
                                    processed_files_count += 1
                                    print(f"Successfully processed document file: {file_path}")
                                else:
                                    print(f"Document processor returned no content for: {file_path}")
                            except Exception as e:
                                print(f"Error processing document file {file_path}: {str(e)}")
                        continue
                    
                    # Process text-based files
                    if file_extension in [".txt", ".py", ".md", ".html", ".js", ".jsx", ".ts", ".tsx", 
                                     ".css", ".scss", ".sass", ".less", ".json", ".yaml", ".yml", 
                                     ".xml", ".csv", ".sql", ".php", ".rb", ".java", ".c", ".cpp", 
                                     ".h", ".hpp", ".cs", ".go", ".rs", ".swift", ".kt", ".kts", 
                                     ".dart", ".lua", ".pl", ".pm", ".sh", ".bash", ".r", ".groovy", 
                                     ".scala", ".clj", ".coffee", ".ex", ".exs", ".erl", ".hrl", 
                                     ".hs", ".vue", ".svelte", ".ipynb", ".ini", ".toml", ".env", 
                                     ".conf", ".config", ".properties", ".gradle", ".tf", ".tfvars", 
                                     ".graphql", ".gql", ".proto", ".sol", ".m", ".mm", ".plist", 
                                     ".bat", ".ps1", ".vbs", ".asm", ".s", ".d", ".jl", ".elm", 
                                     ".fs", ".fsx", ".dockerfile", ".lock", ".rst", ".adoc", ".wiki",
                                     ".log", ".gitignore", ".editorconfig", ".dart", ".pug", ".jade",
                                     ".nix", ".vim", ".elm", ".dtd", ".xsl", ".xslt"]:
                        try:
                            # Use TextLoader for text-based files
                            loader = TextLoader(file_path)
                            documents = loader.load()
                            text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
                            file_texts = text_splitter.split_documents(documents)
                            texts.extend(file_texts)
                            processed_files_count += 1
                            print(f"Processed text file: {file_path}")
                        except UnicodeDecodeError:
                            print(f"Skipping file with unsupported encoding: {file_path}")
                        except Exception as e:
                            print(f"Error processing text file {file_path}: {str(e)}")
                        continue
                    
                    # Try to process other files as text
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        # Create a Document object
                        document = Document(
                            page_content=content,
                            metadata={
                                "file_path": file_path,
                                "file_name": file
                            }
                        )
                        
                        # Split the document into chunks
                        text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
                        file_texts = text_splitter.split_documents([document])
                        texts.extend(file_texts)
                        processed_files_count += 1
                        print(f"Processed file as text: {file_path}")
                    except UnicodeDecodeError:
                        print(f"Skipping non-text file: {file_path}")
                    except Exception as e:
                        print(f"Error processing file {file_path}: {str(e)}")
                except Exception as e:
                    print(f"Unexpected error with file {file_path}: {str(e)}")
    
    print(f"ZIP processing summary: {processed_files_count} files processed successfully")
    print(f"Document files found: {document_files_count}")
    print(f"Total chunks extracted: {len(texts)}")
    
    return texts