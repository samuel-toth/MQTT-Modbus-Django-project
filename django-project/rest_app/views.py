import json

from rest_framework.exceptions import ValidationError
from .serializers import UserLoginSerializer, UserRegisterSerializer
from django.contrib.auth import login, logout, authenticate
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.authtoken.models import Token
from bson import json_util

from .mqtt_service import MQTTService
from .mongo_service import MongoService

# Create your views here.

mongo_service = MongoService()
mqtt_service = MQTTService()


@api_view(["POST"])
@permission_classes([permissions.AllowAny])
def UserRegisterView(request):
    try:
        data = request.data
        serializer = UserRegisterSerializer(data=data)
        if serializer.is_valid(raise_exception=True):
            user = serializer.save()
            if user:
                return Response(status=status.HTTP_201_CREATED)
    except ValidationError as e:
        return Response(data={"error": e.detail}, status=status.HTTP_400_BAD_REQUEST)
    except Exception:
        return Response(
            data={"error": "An error occurred"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])
@permission_classes([permissions.AllowAny])
def UserLoginView(request):
    try:
        data = request.data
        serializer = UserLoginSerializer(data=data)
        if serializer.is_valid(raise_exception=True):
            clean_data = serializer.validated_data
            user = authenticate(
                username=clean_data["username"], password=clean_data["password"]
            )
            if user is not None:
                login(request, user)
                token, created = Token.objects.get_or_create(user=user)
                return Response({"token": token.key}, status=status.HTTP_200_OK)
            else:
                return Response(
                    {"error": "Invalid Credentials"},
                    status=status.HTTP_401_UNAUTHORIZED,
                )
    except ValidationError as e:
        return Response(data={"error": e.detail}, status=status.HTTP_400_BAD_REQUEST)
    except Exception:
        return Response(
            data={"error": "An error occurred"}, status=status.HTTP_400_BAD_REQUEST
        )


@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def UserLogoutView(request):
    try:
        request.user.auth_token.delete()
        logout(request)
        return Response(status=status.HTTP_205_RESET_CONTENT)
    except Exception:
        return Response(
            data={"error": "An error occurred"}, status=status.HTTP_400_BAD_REQUEST
        )


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def GetMQTTDataView(request):
    try:
        data = mongo_service.find_all()

        return Response(
            {
                "type": "success",
                "message": "Data fetched successfully",
                "data": json.loads(json_util.dumps(data)),
            },
            status=status.HTTP_200_OK,
        )
    except Exception:
        return Response(
            data={"error": "An error occurred"}, status=status.HTTP_400_BAD_REQUEST
        )


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def GetMQTTDeviceDataView(request):
    try:
        device_id = request.data["device_id"]
        if device_id is None:
            return Response(
                {"error": "device_id is required"}, status=status.HTTP_400_BAD_REQUEST
            )
        else:
            data = mongo_service.find_by_device_id(device_id)

            return Response(
                {"data": json.loads(json_util.dumps(data))}, status=status.HTTP_200_OK
            )
    except Exception as e:
        return Response(
            data={"error": "An error occurred"}, status=status.HTTP_400_BAD_REQUEST
        )


@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def SendMQTTCommandView(request):
    try:
        data = request.data
        device_id = data["device_id"]
        command = data["command"]

        mqtt_service.send_command(device_id, command)
        return Response(status=status.HTTP_200_OK)
    except Exception:
        return Response(
            data={"error": "An error occurred"}, status=status.HTTP_400_BAD_REQUEST
        )
