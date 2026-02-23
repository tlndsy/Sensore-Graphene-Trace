from django.urls import path
from . import views

app_name = 'administrator'

urlpatterns = [
    path("", views.home, name="home"),
    path("createUser", views.create_user, name="createUser"),
]