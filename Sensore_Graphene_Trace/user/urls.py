from django.urls import path,include
from . import views
from .views import complete_profile, redirect_to_home

app_name = 'user'


urlpatterns = [
    path("home/", views.home, name="home"),
    path('patient/', include("patient.urls")),
    path('administrator/', include("administrator.urls")),
    path('messages/<int:conversation_id>/', views.get_messages, name='get_messages'),
    path('conversation/', views.get_or_create_conversation, name='get_conversation'),
    path('send/', views.send_message, name='send_message'),
    path('unread/', views.unread_count, name='unread_count'),
    path('clinician/', include("clinician.urls")),
    path("complete-profile/", complete_profile, name="complete_profile"),
    path("redirect-to-home/", redirect_to_home, name="redirect_to_home"),
    path("logout-user/", views.logout_user, name="logout_user"),
]
