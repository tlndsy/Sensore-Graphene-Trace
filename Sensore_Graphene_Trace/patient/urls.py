from django.urls import path
from . import views

app_name = 'patient'

urlpatterns = [
    path("stats/", views.stats, name="stats"),
    path("report/", views.interpreterDisplay, name="report"),
]