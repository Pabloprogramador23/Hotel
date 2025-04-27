from django.urls import path
from .views import reservation_list

urlpatterns = [
    path('reservations/', reservation_list, name='reservation-list'),
]