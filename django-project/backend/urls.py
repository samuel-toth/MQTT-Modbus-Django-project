from django.contrib import admin
from django.urls import path
from rest_app import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/register', views.UserRegister),
    path('api/login', views.UserLogin),
    path('api/logout', views.UserLogout),
    path('api/mqtt/data', views.MQTTData),
    path('api/mqtt/data/device', views.MQTTDataDevice),
    path('api/mqtt/command', views.MQTTCommand),
]
