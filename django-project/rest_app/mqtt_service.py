import os
import ssl

from paho.mqtt.client import Client
from dotenv import load_dotenv

load_dotenv()


class MQTTService:
    def __init__(
        self,
        broker=os.getenv("MQTT_BROKER"),
        port=int(os.getenv("MQTT_PORT")),
        username=os.getenv("MQTT_USERNAME"),
        password=os.getenv("MQTT_PASSWORD"),
    ):
        self.client = Client()
        self.client.tls_set(
            ca_certs=os.getenv("MQTT_CA_CERT_PATH"),
            tls_version=ssl.PROTOCOL_TLS,
        )
        self.client.username_pw_set(username, password)
        self.client.connect(broker, port)
        self.client.loop_start()

    def send_command(self, device_id, command):
        topic = os.getenv("MQTT_COMMAND_TOPIC") + "/" + device_id
        self.client.publish(topic, command)
