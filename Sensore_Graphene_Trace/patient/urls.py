from django.urls import path
from . import views

app_name = 'patient'

urlpatterns = [
    path("", views.home, name="home"),
    path("stats/", views.stats, name="stats"),
    path("logout/", views.temp_logout, name="logout"),
]