from django.urls import path
from . import views
from .views import AdminUserListView, AdminUserUpdateView

app_name = 'administrator'

urlpatterns = [
    path("", views.home, name="home"),
    path("createUser", views.create_user, name="createUser"),
    path('users/', AdminUserListView.as_view(), name='user_list'),
    path("users/<uuid:pk>/edit/", AdminUserUpdateView.as_view(), name="user_edit"),
]