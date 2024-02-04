# Integrating MQTT, Modbus, and Django

## Description

This project is an example of a system that uses MQTT, Modbus, and Django to collect, process, and store data. It consists of several layers that work together to achieve this goal:

### MQTT Client and Persistence

The MQTT client in this project is responsible for publishing cryptocurrency data to an MQTT broker. The client subcribes to a command topic and listens for commands to start or stop the data publishing.

The MQTT persistence layer ensures that the data published to the broker is stored in Mongo database.

### Modbus Server and Client Layer

The Modbus server in this project simulate a Modbus server that fetch cryptocurrency data from the CoinCap API.
The server is responsible for storing the data in the registers and making it available to the Modbus client.

The Modbus client is responsible for communicating with the Modbus server and retrieving the data from the registers. The values are stored in the Mongo database.

### Django Backend and REST APIs

The Django backend provides REST APIs to retrieve the data stored in the Mongo database. Authentication is required to access the APIs. User details are stored in Postgres database. The APIs are used to retrieve the data from the database in JSON format.

## Installation

1. Clone the repository
2. Install the dependencies using `pip install -r requirements.txt`
3. Install MongoDB and start the server
4. Install Postgres and start the database
5. Install Mosquitto MQTT broker and start the service
6. Fill in the environment variables in the `.env` file
7. Run the migrations using `python manage.py makemigrations` and `python manage.py migrate


## Usage

1. Start the MQTT client using `python mqtt_client.py` and the MQTT persistence using `python mqtt_persistence.py`
2. Start the Modbus server using `python modbus_server.py` and the Modbus client using `python modbus_client.py`
6. Start the Django backend using `python manage.py runserver`
7. Access the REST APIs using the URL `http://localhost:8000/api/`