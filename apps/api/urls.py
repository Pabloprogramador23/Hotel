from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import (
    DashboardStatsView, 
    AvailableRoomsView, 
    ReservationListAPIView,
    RoomDetailView,
    RoomListView,
    RoomStatusUpdateView,
    RoomMaintenanceHistoryView,
    ReservationCalendarView,
    reservation_create
)

app_name = 'api'  # Definindo o namespace 'api'

urlpatterns = [
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('dashboard/stats/', DashboardStatsView.as_view(), name='dashboard_stats'),
    path('rooms/available/', AvailableRoomsView.as_view(), name='available_rooms'),
    path('reservations/list/', ReservationListAPIView.as_view(), name='reservation_list'),
    path('reservations/', reservation_create, name='reservation_create'),
    path('reservations/calendar/', ReservationCalendarView.as_view(), name='reservation_calendar'),
    
    # Endpoints para gerenciamento de quartos
    path('rooms/', RoomListView.as_view(), name='room_list'),
    path('rooms/<int:pk>/', RoomDetailView.as_view(), name='room_detail'),
    path('rooms/<int:pk>/change-status/', RoomStatusUpdateView.as_view(), name='room_status_update'),
    path('rooms/<int:pk>/maintenance/', RoomMaintenanceHistoryView.as_view(), name='room_maintenance_history'),
]