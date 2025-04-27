from django.http import JsonResponse
from django.db.models import Count, Q
from datetime import date
from apps.rooms.models import Room
from apps.reservations.models import Reservation
from apps.checkin_checkout.models import CheckIn, CheckOut

def dashboard_stats(request):
    today = date.today()
    
    # Estatísticas de ocupação
    total_rooms = Room.objects.count()
    occupied_rooms = Room.objects.filter(status='occupied').count()
    occupancy_rate = round((occupied_rooms / total_rooms * 100) if total_rooms > 0 else 0, 1)
    
    # Estatísticas de check-in/out
    todays_checkins = Reservation.objects.filter(check_in_date=today).count()
    completed_checkins = CheckIn.objects.filter(date=today).count()
    pending_checkins = todays_checkins - completed_checkins
    
    todays_checkouts = Reservation.objects.filter(check_out_date=today).count()
    completed_checkouts = CheckOut.objects.filter(date=today).count()
    pending_checkouts = todays_checkouts - completed_checkouts
    
    return JsonResponse({
        'occupancy_rate': occupancy_rate,
        'occupied_rooms': occupied_rooms,
        'available_rooms': total_rooms - occupied_rooms,
        'todays_checkins': todays_checkins,
        'completed_checkins': completed_checkins,
        'pending_checkins': pending_checkins,
        'todays_checkouts': todays_checkouts,
        'completed_checkouts': completed_checkouts,
        'pending_checkouts': pending_checkouts,
    })
