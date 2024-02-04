from django.contrib import admin
from django.urls import path
from rest_app import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/register', views.UserRegisterView),
    path('api/login', views.UserLoginView),
    path('api/logout', views.UserLogoutView),
    path('api/mqtt/data', views.GetMQTTDataView),
    path('api/mqtt/data/device', views.GetMQTTDeviceDataView),
    path('api/mqtt/command', views.SendMQTTCommandView),
    path('api/modbus/data', views.GetModbusDataView),
    path('api/modbus/data/timestamp', views.GetModbusDataByTimestampView),
]
