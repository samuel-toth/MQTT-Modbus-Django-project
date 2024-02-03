import os
import json
import logging
import argparse

import paho.mqtt.client as mqtt

from functools import partial
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

class MQTTMongoDBBridge:
    def __init__(
        self,
        broker_host,
        broker_port,
        topic,
        mongo_host,
        mongo_port,
        mongo_db,
        mongo_collection,
    ):
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.topic = topic

        self.mongo_client = MongoClient(mongo_host, mongo_port)
        self.db = self.mongo_client[mongo_db]
        self.collection = self.db[mongo_collection]

        self.mqtt_client = mqtt.Client()
        self.mqtt_client.username_pw_set(
            username=os.getenv("MQTT_USERNAME"), password=os.getenv("MQTT_PASSWORD")
        )

        self.mqtt_client.on_connect = partial(self.on_connect)
        self.mqtt_client.on_message = partial(self.on_message)

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            logging.info(f"Connected to broker {self.broker_host}")
            self.mqtt_client.subscribe(self.topic + "/+")
            logging.info(f"Subscribed to topic {self.topic}")
        else:
            logging.error(f"Failed to connect to broker, return code {rc}")

    def on_message(self, client, userdata, msg):
        try:
            data = json.loads(msg.payload.decode())
            data["device_id"] = msg.topic.split("/")[-1]
            self.collection.insert_one(data)
            logging.info(
                f"Received data from device {data['device_id']}, inserting to MongoDB"
            )
        except Exception as e:
            logging.error(f"Failed to insert data with error: {e}")

    def run(self):
        self.mqtt_client.connect(self.broker_host, self.broker_port)
        logging.info(f"Starting MQTT client")
        try:
            self.mqtt_client.loop_forever(
                timeout=10, max_packets=1, retry_first_connection=True
            )
        except KeyboardInterrupt:
            logging.info(f"Service interrupted by keyboard")
        finally:
            self.mqtt_client.disconnect()
            self.mongo_client.close()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )

    parser = argparse.ArgumentParser(
        description="Service for persisting MQTT data to MongoDB"
    )
    parser.add_argument(
        "--broker_host", type=str, default="localhost", help="The MQTT broker address"
    )
    parser.add_argument(
        "--broker_port", type=int, default=1883, help="The MQTT broker port"
    )
    parser.add_argument(
        "--topic",
        type=str,
        default="crypto/data",
        help="The MQTT topic to subscribe to",
    )
    parser.add_argument(
        "--mongo_host", type=str, default="localhost", help="The MongoDB host address"
    )
    parser.add_argument(
        "--mongo_port", type=int, default=27017, help="The MongoDB port"
    )
    args = parser.parse_args()

    try:
        bridge = MQTTMongoDBBridge(
            broker_host=args.broker_host,
            broker_port=args.broker_port,
            topic=args.topic,
            mongo_host=args.mongo_host,
            mongo_port=args.mongo_port,
            mongo_db=os.getenv("MONGO_DB"),
            mongo_collection=os.getenv("MONGO_COLLECTION"),
        )
        bridge.run()
    except KeyboardInterrupt:
        logging.info(f"Service interrupted by keyboard")
