from django.urls import path
from . import views

app_name = 'rooms'  # Adicionando namespace para o app rooms

urlpatterns = [
    path('', views.room_list, name='list'),
]