# clinician/urls.py
from django.urls import path
from . import views

from django.urls import path
from . import views

app_name = 'clinician'
urlpatterns = [
    path("report/", views.reportDisplay, name="report"),
]