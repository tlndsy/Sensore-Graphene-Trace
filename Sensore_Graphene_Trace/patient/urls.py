from django.urls import path
from . import views

app_name = 'patient'

urlpatterns = [
    path("", views.home, name="home"),
    path("view-devices/", views.viewDevices, name="viewDevices"),
    path("register-device/", views.registerDevice, name="registerDevice"),
    path("stats/", views.stats, name="stats"),
    path("logout/", views.temp_logout, name="logout"),
]