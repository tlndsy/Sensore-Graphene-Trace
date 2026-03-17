# patient/urls.py
from django.urls import path
from . import views

from django.urls import path
from . import views

app_name = 'patient'

urlpatterns = [
    path("", views.home, name="home"),
    path('upload/', views.upload_csv, name='upload_csv'),
    path("profile/", views.profile, name="profile"),
    path("view-devices/", views.viewDevices, name="viewDevices"),
    path("register-device/", views.registerDevice, name="registerDevice"),
    path("stats/", views.stats, name="stats"),
    path("report/", views.interpreterDisplay, name="report"),
    path("notifications/", views.notifications, name="stats"),
    path("messages/", views.messages, name="stats"),
    path("logout/", views.temp_logout, name="logout"),
    path("graphs/", views.view_graph, name="graphs"),
    path("report/patient-button", views.interpreterButton, name="interpreterButton"),
]