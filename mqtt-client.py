import os
import ssl
import time
import json
import random
import logging
import argparse
import requests

import paho.mqtt.client as mqtt

from dotenv import load_dotenv

load_dotenv()


class MQTTCryptoClient:
    """
    A class representing an MQTT client for publishing crypto data.

    This client fetches crypto data from CoinCap API and publishes
    it to an MQTT broker at a specified interval.

    Args:
        broker (str): The MQTT broker address.
        port (int): The MQTT broker port.
        username (str): The username for authentication.
        password (str): The password for authentication.
        data_topic (str): The MQTT topic for publishing data.
        command_topic (str): The MQTT topic for receiving commands.
        interval (int): The interval (in seconds) between data publishing.
    """

    def __init__(
        self, broker, port, username, password,
        data_topic, command_topic, interval
    ):
        self.broker = broker
        self.port = port
        self.username = username
        self.password = password
        self.client = mqtt.Client(
            "cryptodev" + time.strftime("%H%M") +
            str(random.randint(0, 1000)).zfill(4)
        )
        self.client.tls_set(
            ca_certs=os.getenv("MQTT_CA_CERT_PATH"),
            tls_version=ssl.PROTOCOL_TLS,
        )
        self.client.username_pw_set(
            username=self.username, password=self.password)
        self.running = True
        self.publishing = True
        self.data_topic = data_topic+"/"+self.client._client_id.decode()
        self.command_topic = command_topic+"/"+self.client._client_id.decode()
        self.interval = interval

        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

        logging.info(
            "MQTT client initialized, ID: %s" % self.client._client_id.decode()
        )

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            logging.info("Connected to broker %s" % self.broker)
            self.client.subscribe(self.command_topic)
            logging.info("Subscribed to command topic %s" %
                         self.command_topic)
        else:
            logging.error("Failed to connect with error: %s" % rc)

    def on_message(self, client, userdata, msg):

        logging.info("Received command %s" % msg.payload.decode())
        if msg.payload.decode() == "client_stop":
            logging.info("Stopping client")
            self.running = False
        elif msg.payload.decode() == "publish_start":
            logging.info("Starting publishing")
            self.publishing = True
        elif msg.payload.decode() == "publish_stop":
            logging.info("Stopping publishing")
            self.publishing = False
        else:
            logging.error("Invalid command %s" % msg.payload.decode())

    def run(self):
        self.client.connect(self.broker, self.port)
        self.client.loop_start()
        logging.info("Client loop started")
        try:
            while self.running:
                if self.publishing:
                    self.publish_data()
                time.sleep(int(self.interval))
        except Exception as e:
            logging.error("Client error: %s" % e)
        finally:
            self.client.disconnect()
            logging.info("Client disconnected")

    def publish_data(self):
        try:
            data = self.fetch_data()
            if data:
                self.client.publish(self.data_topic, json.dumps(data))
                logging.info("Published data to topic %s" % self.data_topic)
        except Exception as e:
            logging.error("Failed to publish data with error: %s" % e)

    def fetch_data(self):
        try:
            response = requests.get(os.getenv("COINCAP_API_URL") + "?limit=10")
            data = response.json()
            timestamp = data.get("timestamp")
            cryptos = [
                {
                    "id": item["id"],
                    "symbol": item["symbol"],
                    "priceUsd": item["priceUsd"],
                }
                for item in data.get("data", [])
            ]
            return {"timestamp": timestamp, "crypto": cryptos}
        except requests.RequestException as e:
            logging.error("Failed to fetch data with error: %s" % e)
            return None


if __name__ == "__main__":

    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )

    parser = argparse.ArgumentParser(description="MQTT Crypto Client")
    parser.add_argument(
        "--broker",
        type=str,
        default="localhost",
        help="The MQTT broker address, default is localhost",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=1883,
        help="The MQTT broker port, default is 1883"
    )
    parser.add_argument(
        "--topic",
        type=str,
        default="crypto/data",
        help="The MQTT topic to publish data, default is crypto/data",
    )
    parser.add_argument(
        "--command",
        type=str,
        default="crypto/command",
        help="The MQTT topic to receive commands, default is crypto/command",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=60,
        help="Interval in seconds to publish data, default is 60",
    )
    args = parser.parse_args()

    try:
        client = MQTTCryptoClient(
            args.broker,
            args.port,
            os.getenv("MQTT_USERNAME"),
            os.getenv("MQTT_PASSWORD"),
            args.topic,
            args.command,
            args.interval,
        )
        client.run()
    except KeyboardInterrupt:
        logging.info("Client stopped via keyboard interrupt")
