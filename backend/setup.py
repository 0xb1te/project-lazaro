from setuptools import setup, find_packages

setup(
    name="L.A.Z.A.R.O",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        # Core Framework Dependencies
        "flask",
        "flask-cors",
        "waitress",
        
        # LangChain and Related
        "langchain",
        "langchain_community",
        "langchain-ollama",
        
        # Vector Database
        "qdrant-client",
        
        # Machine Learning & Embeddings
        "sentence-transformers",
        "numpy",
        
        # Document Processing
        "pypdf",
        "docx2txt",
        "mammoth",
        "python-pptx",
        
        # Utilities
        "python-dotenv",
        "requests"
    ],
    python_requires='>=3.8',
    description="Code query application using hexagonal architecture",
    author="0xb1te",
    author_email="your.email@example.com",
)
