import os
import time
import logging
import argparse

from pymongo import MongoClient
from pymodbus.client import ModbusTcpClient
from pymodbus.exceptions import ModbusException
from pymodbus.payload import BinaryPayloadDecoder, Endian


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
        interval (int): The interval in seconds between each reading and persistence.
    """

    def __init__(
        self,
        modbus_host,
        modbus_port,
        mongo_host,
        mongo_port,
        mongo_db,
        mongo_collection,
        interval,
    ):

        self.modbus_client = ModbusTcpClient(modbus_host, modbus_port)

        self.mongo_client = MongoClient(mongo_host, mongo_port)
        self.db = self.mongo_client[mongo_db]
        self.collection = self.db[mongo_collection]

        self.interval = interval

        if self.modbus_client.connect():
            logging.info(f"Connected to Modbus server")
        else:
            raise ModbusException(f"Failed to connect to Modbus server")

    def run(self):
        try:
            while True:
                response = self.modbus_client.read_holding_registers(
                    address=0, count=2, slave=0x01
                )
                if not response.isError():
                    builder = BinaryPayloadDecoder.fromRegisters(
                        response.registers, byteorder=Endian.LITTLE
                    )

                    decoded_value = builder.decode_32bit_float()

                    self.collection.insert_one({"value": decoded_value})
                    logging.info(
                        f"Value {decoded_value} persisted to database")
                time.sleep(int(self.interval))
        except Exception as e:
            logging.error(f"Client error: {e}")
        finally:
            logging.info(f"Stoping client")
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
        "--mongo_host", type=str, default="localhost", help="The MongoDB host address"
    )
    parser.add_argument(
        "--mongo_port", type=int, default=27017, help="The MongoDB port"
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=60,
        help="Interval in seconds to read and persist data, default is 60",
    )
    args = parser.parse_args()

    try:
        modbus_client = ModbusPersistenceClient(
            modbus_host=args.modbus_host,
            modbus_port=args.modbus_port,
            mongo_host=args.mongo_host,
            mongo_port=args.mongo_port,
            mongo_db=os.getenv("MONGO_DB"),
            mongo_collection=os.getenv("MONGO_COLLECTION"),
            interval=args.interval,
        )

        modbus_client.run()
    except KeyboardInterrupt:
        modbus_client.close_connections()
        logging.info(f"Service stopped via keyboard interrupt")
