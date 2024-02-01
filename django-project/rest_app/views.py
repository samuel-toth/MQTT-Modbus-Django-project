import json
from .serializers import UserLoginSerializer, UserRegisterSerializer
from django.contrib.auth import login, logout, authenticate
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.authtoken.models import Token
import pymongo as mongoclient
import paho.mqtt.client as mqtt
import os


# Create your views here.

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def UserRegister(request):
	try :
		data = request.data
		serializer = UserRegisterSerializer(data=data)
		if serializer.is_valid(raise_exception=True):
			user = serializer.save()
			if user:
				return Response(status=status.HTTP_201_CREATED)
	except Exception as e:
		return Response(data=e, status=status.HTTP_400_BAD_REQUEST)
	

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def UserLogin(request):
    try:
        data = request.data
        serializer = UserLoginSerializer(data=data)
        if serializer.is_valid(raise_exception=True):
            clean_data = serializer.validated_data
            user = authenticate(username=clean_data['username'], password=clean_data['password'])
            if user is not None:
                login(request, user)
                token, created = Token.objects.get_or_create(user=user)
                return Response({'token': token.key}, status=status.HTTP_200_OK)
            else:
                return Response({'error': 'Invalid Credentials'}, status=status.HTTP_401_UNAUTHORIZED)
    except Exception as e:
        return Response(data=e, status=status.HTTP_400_BAD_REQUEST)



@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def UserLogout(request):
    try:
        request.user.auth_token.delete()
        logout(request)
        return Response(status=status.HTTP_205_RESET_CONTENT)
    except Exception as e:
        return Response(data=e, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def MQTTData(request):
    try:
        device_id = request.GET.get('device_id')
        if device_id is None:
            return Response({'error': 'device_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            data = collection.find({'device_id': device_id})
            return Response({'data': data}, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response(data=e, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def MQTTCommand(request):
    try:
        data = request.data
        device_id = data['device_id']
        command = data['command']
        mqtt_client.publish(MQTT_TOPIC, json.dumps({'device_id': device_id, 'command': command}))
        return Response(status=status.HTTP_200_OK)
    except Exception as e:
        return Response(data=e, status=status.HTTP_400_BAD_REQUEST)
    

# MongoDB Parameters
MONGO_HOST = "localhost"
MONGO_PORT = 27017
MONGO_DB = "mqtt-db"
MONGO_COLLECTION = "mqtt-data"

mongo_client = mongoclient.MongoClient(MONGO_HOST, MONGO_PORT)
db = mongo_client[MONGO_DB]
collection = db[MONGO_COLLECTION]

# MQTT Parameters

MQTT_BROKER = os.getenv("MQTT_BROKER")
MQTT_PORT = os.getenv("MQTT_PORT")
MQTT_TOPIC = os.getenv("MQTT_TOPIC")
MQTT_USERNAME = os.getenv("MQTT_USERNAME")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD")

mqtt_client = mqtt.Client()
mqtt_client.username_pw_set(username=MQTT_USERNAME, password=MQTT_PASSWORD)
mqtt_client.connect(MQTT_BROKER, MQTT_PORT)