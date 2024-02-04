import os
import ssl
import time
import logging
import argparse

from pymongo import MongoClient
from pymodbus.client import ModbusTlsClient
from pymodbus.exceptions import ModbusException
from pymodbus.payload import BinaryPayloadDecoder, Endian
from dotenv import load_dotenv

load_dotenv()


class ModbusPersistenceClient:
    """
    A class representing a Modbus persistence client.

    This client connects to a Modbus server, reads holding registers
    and persists the values to a MongoDB database at a specified interval.

    Args:
        modbus_host (str): The host address of the Modbus server.
        modbus_port (int): The port number of the Modbus server.
        mongo_host (str): The host address of the MongoDB server.
        mongo_port (int): The port number of the MongoDB server.
        mongo_db (str): The name of the MongoDB database.
        mongo_collection (str): The name of the MongoDB collection.
        interval (int): The interval in seconds between each reading
        and persistence.
    """

    def __init__(
        self,
        modbus_host,
        modbus_port,
        mongo_uri,
        mongo_db,
        mongo_collection,
        interval,
    ):

        ssl_context = ssl.create_default_context(
            ssl.Purpose.SERVER_AUTH, cafile=os.getenv("MODBUS_CA_CERT_PATH")
        )

        ssl_context.load_cert_chain(
            certfile=os.getenv("MODBUS_CLIENT_CERT_PATH"),
            keyfile=os.getenv("MODBUS_CLIENT_KEY_PATH"),
        )

        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE

        self.modbus_client = ModbusTlsClient(
            host=modbus_host,
            port=modbus_port,
            sslctx=ssl_context,
            server_hostname="localhost",
        )

        self.mongo_client = MongoClient(mongo_uri)
        self.db = self.mongo_client[mongo_db]
        self.collection = self.db[mongo_collection]

        self.interval = interval

        if self.modbus_client.connect():
            logging.info("Connected to Modbus server")
        else:
            raise ModbusException("Failed to connect to Modbus server")

    def run(self):
        try:
            while True:

                response = self.modbus_client.read_holding_registers(
                    0, 20, unit=1)
                if not response.isError():
                    decoded_values = []
                    for i in range(0, len(response.registers), 2):
                        builder = BinaryPayloadDecoder.fromRegisters(
                            [response.registers[i], response.registers[i + 1]],
                            byteorder=Endian.LITTLE,
                        )

                        decoded_values.append(builder.decode_32bit_float())

                    ranked_values = {
                        str(i+1): val for i, val in enumerate(decoded_values)
                    }

                    self.collection.insert_one(
                        {"value": ranked_values,
                            "timestamp": int(time.time())}
                    )
                    logging.info("Values persisted to database")
                else:
                    logging.error(f"Modbus error: {response}")
                time.sleep(int(self.interval))
        except Exception as e:
            logging.error(f"Client error: {e}")
        finally:
            logging.info("Stoping client")
            if self.modbus_client:
                self.modbus_client.close()
            if self.mongo_client:
                self.mongo_client.close()


if __name__ == "__main__":

    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )

    parser = argparse.ArgumentParser(
        description="Modbus client for data persistence")
    parser.add_argument(
        "--modbus_host",
        type=str,
        default="localhost",
        help="The Modbus server address, default is localhost",
    )
    parser.add_argument(
        "--modbus_port",
        type=int,
        default=5020,
        help="The Modbus server port, default is 5020",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=60,
        help="Interval in seconds to read and persist data, default is 60",
    )
    args = parser.parse_args()

    try:
        mb_persistence_client = ModbusPersistenceClient(
            modbus_host=args.modbus_host,
            modbus_port=args.modbus_port,
            mongo_uri=os.getenv("MONGO_URI"),
            mongo_db=os.getenv("MONGO_DB"),
            mongo_collection=os.getenv("MODBUS_MONGO_COLLECTION"),
            interval=args.interval,
        )
        mb_persistence_client.run()
    except KeyboardInterrupt:
        logging.info("Service stopped via keyboard interrupt")
        mb_persistence_client.modbus_client.close()
        mb_persistence_client.mongo_client.close()
