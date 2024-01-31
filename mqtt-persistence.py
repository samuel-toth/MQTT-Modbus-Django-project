import paho.mqtt.client as mqtt
import pymongo as mongoclient
import time
import json
import os
from dotenv import load_dotenv

load_dotenv()

# MongoDB Parameters
MONGO_HOST = os.getenv("MONGO_HOST")
MONGO_PORT = int(os.getenv("MONGO_PORT"))
MONGO_DB = os.getenv("MONGO_DB")
MONGO_COLLECTION = os.getenv("MONGO_COLLECTION")

# MQTT Parameters
MQTT_BROKER = os.getenv("MQTT_BROKER")
MQTT_PORT = int(os.getenv("MQTT_PORT"))
MQTT_TOPIC = os.getenv("MQTT_TOPIC")
MQTT_USERNAME = os.getenv("MQTT_USERNAME")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD")


def connect_mqtt():
    """
    Connects to the MQTT broker and sets up the necessary callbacks for message handling.

    Returns:
        client (mqtt.Client): The MQTT client object.
    """
    def on_message(client, userdata, msg):
        try:
            print("Received data from topic `%s`" % msg.topic +
                  " at " + time.strftime("%H:%M:%S", time.localtime()))
            data = json.loads(msg.payload.decode())
            collection.insert_one(data)
            print("Inserted data to MongoDB")
        except Exception as e:
            print("Failed while inserting with error: %s" % e)

    def on_connect(client, userdata, flags, rc):
        try:
            if rc == 0:
                print("Connected to MQTT Broker!")
            else:
                raise Exception("Error code %d\n", rc)
        except Exception as e:
            print("Failed to connect with error: %s" % e)

    client = mqtt.Client()
    client.username_pw_set(username=MQTT_USERNAME, password=MQTT_PASSWORD)
    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(MQTT_BROKER, MQTT_PORT)

    return client


# Connect to MongoDB
mongo_client = mongoclient.MongoClient(MONGO_HOST, MONGO_PORT)
db = mongo_client[MONGO_DB]
collection = db[MONGO_COLLECTION]

if __name__ == '__main__':
    client = connect_mqtt()
    client.loop_forever(retry_first_connection=True)

    client.subscribe(MQTT_TOPIC)
    print("Subscribed to topic `%s`" % MQTT_TOPIC)
