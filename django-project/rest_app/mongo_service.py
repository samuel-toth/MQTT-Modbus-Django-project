import os

from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

MONGO_HOST = os.getenv("MONGO_HOST")
MONGO_PORT = os.getenv("MONGO_PORT")
MONGO_DB = os.getenv("MONGO_DB")
MONGO_COLLECTION = os.getenv("MONGO_COLLECTION")


class MongoService:

    def __init__(
        self, host=MONGO_HOST, port=MONGO_PORT, db=MONGO_DB, collection=MONGO_COLLECTION
    ):
        self.host = host
        self.port = port
        self.db = db
        self.collection = collection
        self.client = MongoClient(self.host, self.port)
        self.db = self.client[self.db]
        self.collection = self.db[self.collection]

    def find_all(self):
        return list(self.collection.find())

    def find_by_device_id(self, device_id):
        return list(self.collection.find({"device_id": device_id}))
