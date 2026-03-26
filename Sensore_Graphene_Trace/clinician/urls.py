# clinician/urls.py
from django.urls import path
from . import views

from django.urls import path
from . import views

app_name = 'clinician'
urlpatterns = [
    #path('', views.displayProfile, name='profile'),
    path("report/", views.reportDisplay, name="report"),
    path("profile/", views.displayProfile, name="profile"),
]