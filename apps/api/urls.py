from django.urls import path
from . import views

app_name = 'api'  # Definindo o namespace 'api'

urlpatterns = [
    path('dashboard/stats/', views.dashboard_stats, name='dashboard_stats'),
    path('available-rooms/', views.available_rooms, name='available_rooms'),
    path('reservations/', views.reservation_create, name='reservation_create'),
]