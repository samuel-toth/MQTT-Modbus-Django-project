import os

from paho.mqtt.client import Client
from dotenv import load_dotenv

load_dotenv()

MQTT_BROKER = os.getenv("MQTT_BROKER") or "localhost"
MQTT_PORT = int(os.getenv("MQTT_PORT")) or 1883
MQTT_DATA_TOPIC = os.getenv("MQTT_DATA_TOPIC") or "mqttdata"
MQTT_COMMAND_TOPIC = os.getenv("MQTT_COMMAND_TOPIC") or "mqttcommand"
MQTT_USERNAME = os.getenv("MQTT_USERNAME")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD")


class MQTTService:
    def __init__(
        self,
        broker=MQTT_BROKER,
        port=MQTT_PORT,
        username=MQTT_USERNAME,
        password=MQTT_PASSWORD,
    ):
        self.broker = broker
        self.port = port
        self.username = username
        self.password = password
        self.client = Client()
        self.client.username_pw_set(username, password)
        self.client.connect(broker, port)
        self.client.loop_start()

    def send_command(self, device_id, command):
        topic = MQTT_COMMAND_TOPIC + "/" + device_id
        self.client.publish(topic, command)
