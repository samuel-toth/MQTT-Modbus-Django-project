import os

from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

MONGO_HOST = os.getenv("MONGO_HOST")
MONGO_PORT = int(os.getenv("MONGO_PORT"))
MONGO_DB = os.getenv("MONGO_DB")
MQTT_MONGO_COLLECTION = os.getenv("MQTT_MONGO_COLLECTION")
MODBUS_MONGO_COLLECTION = os.getenv("MODBUS_MONGO_COLLECTION")


class MongoService:

    def __init__(
        self,
        host=MONGO_HOST,
        port=MONGO_PORT,
        db=MONGO_DB,
        mqtt_col=MQTT_MONGO_COLLECTION,
        mb_col=MODBUS_MONGO_COLLECTION,
    ):
        self.client = MongoClient(host, port)
        self.db = self.client[db]
        self.mb_col = self.db[mqtt_col]
        self.mqtt_col = self.db[mb_col]

    def find_all_mqtt_data(self):
        return list(self.mqtt_col.find())

    def find_by_device_id(self, device_id):
        return list(self.mqtt_col.find({"device_id": device_id}))

    def find_all_modbus_data(self):
        return list(self.mb_col.find())

    def find_modbus_data_by_timestamp(self, timestamp):
        return list(self.mb_col.find({"timestamp": timestamp}))
