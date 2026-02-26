from django.urls import path, include
from . import views

app_name = 'user'

urlpatterns = [
    path("home/", views.home, name="home"),
    path('patient/', include("patient.urls")),
]

