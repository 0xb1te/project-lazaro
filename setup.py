from setuptools import setup, find_packages

setup(
    name="code_assistant",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        # Core Framework Dependencies
        "flask",
        "flask-cors",
        "waitress",
        "streamlit",
        
        # LangChain and Related
        "langchain",
        "langchain_community",
        "langchain-ollama",
        
        # Vector Database
        "qdrant-client",
        
        # Machine Learning & Embeddings
        "sentence-transformers",
        
        # Utilities
        "python-dotenv"
    ]
)