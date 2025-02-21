from qdrant_client import QdrantClient
from qdrant_client.http import models

def get_qdrant_db():
    client = QdrantClient(host="localhost", port=6333)
    
    # Create a vector database if it doesn't exist
    client.recreate_collection(
        collection_name="code_vectors",
        vectors_config=models.VectorParams(size=1024, distance=models.Distance.COSINE),
    )
    
    return client

def add_vector(client, text, embedding):
    point = models.PointStruct(
        id=models.ID("doc_" + str(uuid.uuid1())),
        vector=embedding,
        payload={"text": text}
    )
    client.upsert(collection_name="code_vectors", points=[point])