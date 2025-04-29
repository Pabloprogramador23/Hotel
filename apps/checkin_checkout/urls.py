from django.urls import path
from . import views

app_name = 'checkin_checkout'

urlpatterns = [
    # Endpoints para check-in e check-out
    path('checkin/<int:reservation_id>/', views.perform_checkin, name='perform_checkin'),
    path('checkout/<int:reservation_id>/', views.perform_checkout, name='perform_checkout'),
    
    # Endpoints para listagens
    path('current-guests/', views.list_current_guests, name='list_current_guests'),
    path('expected-arrivals/', views.list_expected_arrivals, name='list_expected_arrivals'),
    path('expected-departures/', views.list_expected_departures, name='list_expected_departures'),
]