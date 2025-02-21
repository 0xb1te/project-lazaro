from setuptools import setup, find_packages

setup(
    name="ollama_mongo_db_vector",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "flask",
        "langchain",
        "pymongo",
        "python-dotenv",
        "ollama",
    ],
)