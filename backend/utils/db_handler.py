import pymongo
from backend.config import MONGO_URI, DB_NAME, COLLECTION_NAME

def get_db_collection():
    client = pymongo.MongoClient(MONGO_URI)
    db = client[DB_NAME]
    collection = db[COLLECTION_NAME]
    return collection