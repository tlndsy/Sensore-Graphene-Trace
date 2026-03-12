from django.urls import path
from . import views

urlpatterns = [
    path("home/", views.home, name="home"),
    path("register/", views.register, name="register")

]

urlpatterns = [
    # ... existing urls ...
    path('messages/<int:conversation_id>/', views.get_messages, name='get_messages'),
    path('conversation/', views.get_or_create_conversation, name='get_conversation'),
    path('send/', views.send_message, name='send_message'),
    path('unread/', views.unread_count, name='unread_count'),
]