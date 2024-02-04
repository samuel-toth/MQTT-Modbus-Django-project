import os

from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()


class MongoService:

    def __init__(
        self,
        db=os.getenv("MONGO_DB"),
        mqtt_col=os.getenv("MQTT_MONGO_COLLECTION"),
        mb_col=os.getenv("MODBUS_MONGO_COLLECTION"),
    ):
        self.client = MongoClient(os.getenv("MONGO_URI"))
        self.db = self.client[db]
        self.mb_col = self.db[mb_col]
        self.mqtt_col = self.db[mqtt_col]

    def find_all_mqtt_data(self):
        return list(self.mqtt_col.find())

    def find_by_device_id(self, device_id):
        return list(self.mqtt_col.find({"device_id": device_id}))

    def find_all_modbus_data(self):
        return list(self.mb_col.find())

    def find_modbus_data_by_timestamp(self, timestamp):
        return list(self.mb_col.find({"timestamp": timestamp}))
