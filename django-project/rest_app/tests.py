from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token
from rest_framework import status
from django.contrib.auth import get_user_model
from unittest.mock import patch
from rest_framework.test import APITestCase

User = get_user_model()


class UserRegisterTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="existinguser", password="password"
        )
        self.data = {
            "username": "newuser",
            "password": "newpassword",
            "password2": "newpassword",
        }

    def test_user_register(self):
        response = self.client.post("/api/register", self.data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_user_register_invalid(self):
        response = self.client.post("/api/register", {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_register_existing(self):
        response = self.client.post(
            "/api/register",
            {
                "username": "existinguser",
                "password": "testpassword",
                "password2": "testpassword",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_register_no_password(self):
        response = self.client.post("/api/register", {"username": "newuser"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_register_password_mismatch(self):
        response = self.client.post(
            "/api/register",
            {"username": "newuser", "password": "password", "password2": "password2"},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class UserLoginTest(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="existinguser", password="password"
        )
        self.data = {"username": "existinguser", "password": "password"}

    def test_user_login(self):
        response = self.client.post("/api/login", self.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_user_login_invalid(self):
        response = self.client.post("/api/login", {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_login_wrong_password(self):
        response = self.client.post(
            "/api/login", {"username": "existinguser",
                           "password": "wrongpassword"}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_login_wrong_username(self):
        response = self.client.post(
            "/api/login", {"username": "wronguser", "password": "password"}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class GetMQTTDataViewTest(APITestCase):

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="existinguser", password="password"
        )
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION="Token " + self.token.key)

    @patch("rest_app.mongo_service.MongoService.find_all_mqtt_data")
    def test_get_mqtt_data_authenticated(self, mock_find_all):
        mock_data = [
            {"device_id": "1", "data": "data1"},
            {"device_id": "2", "data": "data2"},
        ]

        mock_find_all.return_value = mock_data
        response = self.client.get("/api/mqtt/data", {})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["data"], mock_data)
        mock_find_all.assert_called_once()

    def test_get_mqtt_data_not_authenticated(self):
        self.client.credentials()
        response = self.client.get("/api/mqtt/data", {})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(
            response.json()[
                "detail"], "Authentication credentials were not provided."
        )

    def test_get_mqtt_data_invalid_token(self):
        self.client.credentials(HTTP_AUTHORIZATION="Token invalidtoken")
        response = self.client.get("/api/mqtt/data", {})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.json()["detail"], "Invalid token.")


class GetMQTTDeviceDataViewTest(APITestCase):

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="existinguser", password="password"
        )
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION="Token " + self.token.key)

    @patch("rest_app.mongo_service.MongoService.find_by_device_id")
    def test_get_mqtt_device_data_authenticated(self, mock_find_by_device_id):
        mock_data = [
            {"device_id": "1", "data": "data1"},
            {"device_id": "1", "data": "data2"},
        ]
        mock_find_by_device_id.return_value = mock_data

        response = self.client.get("/api/mqtt/data/device", {"device_id": "1"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["data"], mock_data)
        mock_find_by_device_id.assert_called_once_with("1")

    def test_get_mqtt_device_data_not_authenticated(self):
        self.client.credentials()

        response = self.client.get("/api/mqtt/data/device", {"device_id": "1"})

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(
            response.json()[
                "detail"], "Authentication credentials were not provided."
        )

    def test_get_mqtt_device_data_invalid_token(self):
        self.client.credentials(HTTP_AUTHORIZATION="Token invalidtoken")

        response = self.client.get("/api/mqtt/data/device", {"device_id": "1"})

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.json()["detail"], "Invalid token.")

    def test_get_mqtt_device_data_no_device_id(self):
        response = self.client.get("/api/mqtt/data/device", {})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()["error"], "Device ID is required.")


class SendMQTTCommandViewTest(APITestCase):

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="existinguser", password="password"
        )
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION="Token " + self.token.key)

    @patch("rest_app.mqtt_service.MQTTService.send_command")
    def test_send_mqtt_command_authenticated(self, mock_send_command):
        mock_data = {"device_id": "1", "command": "on"}

        response = self.client.post("/api/mqtt/command", mock_data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mock_send_command.assert_called_once_with("1", "on")

    def test_send_mqtt_command_not_authenticated(self):
        self.client.credentials()

        response = self.client.post(
            "/api/mqtt/command", {"device_id": "1", "command": "on"}
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(
            response.json()[
                "detail"], "Authentication credentials were not provided."
        )

    def test_send_mqtt_command_invalid_token(self):
        self.client.credentials(HTTP_AUTHORIZATION="Token invalidtoken")

        response = self.client.post(
            "/api/mqtt/command", {"device_id": "1", "command": "on"}
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.json()["detail"], "Invalid token.")

    def test_send_mqtt_command_no_device_id(self):
        response = self.client.post("/api/mqtt/command", {"command": "on"})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()["error"], "Device ID is required.")

    def test_send_mqtt_command_no_command(self):
        response = self.client.post("/api/mqtt/command", {"device_id": "1"})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()["error"], "Command is required.")


class GetModbusDataViewTest(APITestCase):

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="existinguser", password="password"
        )
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION="Token " + self.token.key)

    @patch("rest_app.mongo_service.MongoService.find_all_modbus_data")
    def test_get_modbus_data_authenticated(self, mock_find_all_modbus_data):
        mock_data = [
            {"device_id": "1", "data": "data1"},
            {"device_id": "2", "data": "data2"},
        ]

        mock_find_all_modbus_data.return_value = mock_data
        response = self.client.get("/api/modbus/data", {})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["data"], mock_data)
        mock_find_all_modbus_data.assert_called_once()

    def test_get_modbus_data_not_authenticated(self):
        self.client.credentials()
        response = self.client.get("/api/modbus/data", {})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(
            response.json()[
                "detail"], "Authentication credentials were not provided."
        )

    def test_get_modbus_data_invalid_token(self):
        self.client.credentials(HTTP_AUTHORIZATION="Token invalidtoken")
        response = self.client.get("/api/modbus/data", {})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.json()["detail"], "Invalid token.")


class GetModbusDataByTimestampViewTest(APITestCase):

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="existinguser", password="password"
        )
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION="Token " + self.token.key)

    @patch("rest_app.mongo_service.MongoService.find_modbus_data_by_timestamp")
    def test_get_modbus_data_by_timestamp_authenticated(self, mock_find_by_timestamp):
        mock_data = [
            {"timestamp": 1706544941355, "value": "data1"},
            {"timestamp": 1706544941354, "value": "data2"},
        ]
        mock_find_by_timestamp.return_value = mock_data

        response = self.client.get(
            "/api/modbus/data/timestamp", {"timestamp": 1706544941355})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["data"], mock_data)
        mock_find_by_timestamp.assert_called_once_with(str(1706544941355))

    def test_get_modbus_data_by_timestamp_not_authenticated(self):
        self.client.credentials()

        response = self.client.get(
            "/api/modbus/data/timestamp", {"timestamp": 1706544941355})

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(
            response.json()[
                "detail"], "Authentication credentials were not provided."
        )

    def test_get_modbus_data_by_timestamp_invalid_token(self):
        self.client.credentials(HTTP_AUTHORIZATION="Token invalidtoken")

        response = self.client.get(
            "/api/modbus/data/timestamp", {"timestamp": 1706544941355})

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.json()["detail"], "Invalid token.")

    def test_get_modbus_data_by_timestamp_no_timestamp(self):
        response = self.client.get("/api/modbus/data/timestamp", {})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()["error"],
                         "UNIX timestamp is required.")

    def test_get_modbus_data_by_timestamp_invalid_timestamp(self):
        response = self.client.get(
            "/api/modbus/data/timestamp", {"timestamp": "invalidtimestamp"})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()["error"],
                         "UNIX timestamp is required.")
