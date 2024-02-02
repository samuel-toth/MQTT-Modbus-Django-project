import argparse
from functools import partial
import paho.mqtt.client as mqtt
import pymongo as mongoclient
import time
import json
import os
from dotenv import load_dotenv
import logging

load_dotenv()

# MongoDB Parameters
MONGO_DB = os.getenv("MONGO_DB")
MONGO_COLLECTION = os.getenv("MONGO_COLLECTION")

# MQTT Parameters
MQTT_USERNAME = os.getenv("MQTT_USERNAME")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD")


def on_connect(client, userdata, flags, rc, topic):
    try:
        if rc == 0:
            logging.info("Connected to broker `%s`" % client._host)
            client.subscribe(topic + "/+")
            logging.info("Subscribed to topic `%s`" % topic)
        else:
            raise Exception("Error code %d\n", rc)
    except Exception as e:
        logging.error("Failed to connect to broker with error: %s" % e)


def on_message(client, userdata, msg, collection):
    try:
        data = json.loads(msg.payload.decode())

        data["device_id"] = msg.topic.split("/")[-1]

        collection.insert_one(data)
        logging.info("Inserted data from device `%s`" % data["device_id"])
    except Exception as e:
        logging.error("Failed to insert data with error: %s" % e)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(message)s')

    parser = argparse.ArgumentParser(
        description="Service for persisting MQTT data to MongoDB")
    parser.add_argument("--brokerhost", type=str, default="localhost",
                        help="The MQTT broker address, default is localhost")
    parser.add_argument("--brokerport", type=int, default=1883,
                        help="The MQTT broker port, default is 1883")
    parser.add_argument("--topic", type=str, default="crypto/data",
                        help="The MQTT topic to subscribe to and persist, default is crypto/data")
    parser.add_argument("--mongohost", type=str, default="localhost",
                        help="The MongoDB host address, default is localhost")
    parser.add_argument("--mongoport", type=int, default=27017,
                        help="The MongoDB port, default is 27017")
    args = parser.parse_args()

    mongo_client = mongoclient.MongoClient(args.mongohost, args.mongoport)
    db = mongo_client[MONGO_DB]
    collection = db[MONGO_COLLECTION]

    mqtt_client = mqtt.Client()
    mqtt_client.username_pw_set(username=MQTT_USERNAME, password=MQTT_PASSWORD)
    mqtt_client.on_connect = partial(on_connect, topic=args.topic)
    mqtt_client.on_message = partial(on_message, collection=collection)

    mqtt_client.connect(args.brokerhost, args.brokerport)
    try:
        mqtt_client.loop_forever(retry_first_connection=True)
    except KeyboardInterrupt:
        logging.info("Service interrupted by keyboard")
    finally:
        mqtt_client.disconnect()
        mongo_client.close()
