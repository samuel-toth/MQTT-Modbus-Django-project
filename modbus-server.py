import os
import ssl
import time
import logging
import argparse
from pymodbus import ModbusException
import requests
import threading

from pymodbus.server import StartTlsServer
from pymodbus.payload import BinaryPayloadBuilder, Endian
from pymodbus.datastore import (
    ModbusSequentialDataBlock,
    ModbusServerContext,
    ModbusSlaveContext,
)
from pymodbus.framer import Framer
from dotenv import load_dotenv

load_dotenv()

class ModbusServer:
    """
    A class representing a Modbus server for fetching and storing Bitcoin price to registers.

    This server fetches the current Bitcoin price from CoinCap API and stores it in a Modbus register at a specified interval.

    Args:
        host (str): The host address of the Modbus server.
        port (int): The port number of the Modbus server.
        interval (int): The interval in seconds between data updates.
    """

    def __init__(self, host, port, interval):
        self.host = host
        self.port = port
        self.running = True
        self.interval = interval

        self.setup_server_context()

    def setup_server_context(self):
        initial_values = [0]
        datablock = ModbusSequentialDataBlock(0, initial_values)

        slave_context = ModbusSlaveContext(
            di=datablock, co=datablock, hr=datablock, ir=datablock
        )
        self.context = ModbusServerContext(slaves=slave_context, single=True)

    def update_registers(self):
        while self.running:
            address = 0
            price = self.fetch_data()

            builder = BinaryPayloadBuilder(byteorder=Endian.LITTLE)
            builder.add_32bit_float(float(price))
            payload = builder.to_registers()

            self.context[0x01].setValues(3, address, payload)
            logging.info(
                f"Updated register values at address {address} with {price} and payload {payload}"
            )
            time.sleep(int(self.interval))

    def run(self):
        logging.info(f"Starting Modbus server at {self.host}:{self.port}")

        ssl_context = ssl.create_default_context(
            ssl.Purpose.CLIENT_AUTH, cafile=os.getenv("MODBUS_CA_CERT_PATH")
        )

        ssl_context.load_cert_chain(
            certfile=os.getenv("MODBUS_SERVER_CERT_PATH"),
            keyfile=os.getenv("MODBUS_SERVER_KEY_PATH"),
        )


        StartTlsServer(
            context=self.context, 
            identity="modbus-server",
            sslctx = ssl_context,
            address=(self.host, self.port),
            framer=Framer.TLS,
            broadcast_enable=True,
            ignore_missing_slaves=True,
        )

    def fetch_data(self):
        try:
            response = requests.get(os.getenv("COINCAP_API_URL") + "/bitcoin")
            data = response.json()
            price = data.get("data").get("priceUsd")
            return price
        except requests.RequestException as e:
            logging.error(f"Failed to fetch data with error: {e}")
            return None


if __name__ == "__main__":

    logging.basicConfig(
        level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s"
    )

    parser = argparse.ArgumentParser(
        description="Modbus server for fetching and storing Bitcoin price to registers"
    )
    parser.add_argument(
        "--host",
        type=str,
        default="localhost",
        help="Host for the Modbus server, default is localhost",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=5020,
        help="Port for the Modbus server, default is 5020",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=60,
        help="Interval in seconds to update register values, default is 10",
    )
    args = parser.parse_args()

    try:
        server = ModbusServer(args.host, args.port, args.interval)
        update_thread = threading.Thread(target=server.update_registers)
        update_thread.start()
        server.run()
    except ModbusException as e:
        logging.error(f"Modbus error: {e}")
    except KeyboardInterrupt:
        logging.info(f"Modbus server stopped by user.")
    finally:
        server.running = False
        update_thread.join()
