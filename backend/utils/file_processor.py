import zipfile
import tempfile
import os
from langchain_community.document_loaders import TextLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain.docstore.document import Document

def process_file(file_path):
    loader = TextLoader(file_path)
    documents = loader.load()
    text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    texts = text_splitter.split_documents(documents)
    return texts

def process_zip_file(zip_path):
    texts = []
    with tempfile.TemporaryDirectory() as temp_dir:
        # Extract the zip file
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)
        
        # Walk through the extracted directory
        for root, _, files in os.walk(temp_dir):
            for file in files:
                file_path = os.path.join(root, file)
                
                try:
                    # Skip binary files (e.g., .pyc, .git objects)
                    if file.endswith((".pyc", ".git", ".bin", ".exe", ".dll", ".so", ".pyc")):
                        print(f"Skipping binary file: {file_path}")
                        continue
                    
                    # Process text-based files
                    if file.endswith((".txt", ".py", ".md", ".html", ".js", ".css", ".json", ".yaml", ".yml")):
                        # Use TextLoader for supported text-based files
                        loader = TextLoader(file_path)
                        documents = loader.load()
                        text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
                        texts.extend(text_splitter.split_documents(documents))
                    else:
                        # For other files, read the content directly
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        # Create a LangChain Document object
                        document = Document(
                            page_content=content,
                            metadata={
                                "file_path": file_path,
                                "file_name": file
                            }
                        )
                        
                        # Split the text into chunks
                        text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
                        texts.extend(text_splitter.split_documents([document]))
                    print(f"Processed file with filename at: ${file_path}")
                except UnicodeDecodeError:
                    print(f"Skipping non-text file (binary or unsupported encoding): {file_path}")
                except Exception as e:
                    print(f"Error processing file {file_path}: {str(e)}")
    
    return texts