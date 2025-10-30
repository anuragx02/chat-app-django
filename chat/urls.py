from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    path('', views.lobby_view, name='lobby'),
    path('room/<slug:slug>/', views.room_view, name='room'),
    path('create/', views.create_room_view, name='create_room'),
    path('private/<int:user_id>/', views.private_chat_view, name='private_chat'),
]
