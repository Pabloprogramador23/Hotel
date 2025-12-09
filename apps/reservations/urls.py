from django.urls import path

from . import views

app_name = 'reservations'


urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('rooms/<int:room_id>/', views.room_detail, name='room_detail'),
    path('check-in/quick/', views.quick_check_in, name='quick_check_in'),
    path('checkout/<int:reservation_id>/', views.checkout, name='checkout'),
    path('guests/<int:guest_id>/payment/', views.update_guest_payment, name='update_guest_payment'),
    path('reservations/<int:reservation_id>/guests/add/', views.add_guest, name='add_guest'),
]