# patient/urls.py
from django.urls import path
from . import views

from django.urls import path
from . import views

app_name = 'patient'

urlpatterns = [
    path("", views.PatientHomeView.as_view(), name="home"),
    path('upload/', views.upload_csv, name='upload_csv'),
    path("profile/", views.profile, name="profile"),
    path("view-devices/", views.PatientViewDevices.as_view(), name="viewDevices"),
    path("register-device/", views.PatientRegisterDeviceView.as_view(), name="registerDevice"),
    path("report/", views.interpreterDisplay, name="report"),
    path("notifications/", views.notifications, name="stats"),
    path("messages/", views.messages, name="stats"),
    path("logout/", views.temp_logout, name="logout"),
    path("graphs/", views.PressureDataView.as_view(), name="graphs"),
    path("report/patient-button", views.interpreterButton, name="interpreterButton"),
]