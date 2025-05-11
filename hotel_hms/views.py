from django.shortcuts import render
from django.db.models import Count, Q
from django.utils import timezone
from datetime import date, datetime
from apps.rooms.models import Room
from apps.reservations.models import Reservation
from apps.checkin_checkout.models import CheckIn, CheckOut

def home(request):
    today = timezone.now().date()
    
    # Estatísticas de ocupação
    total_rooms = Room.objects.count()
    occupied_rooms = Room.objects.filter(status='occupied').count()
    occupancy_rate = round((occupied_rooms / total_rooms * 100) if total_rooms > 0 else 0, 1)
    
    # Estatísticas de check-in/out
    todays_checkins = Reservation.objects.filter(check_in_date=today).count()
    completed_checkins = CheckIn.objects.filter(check_in_time__date=today).count()
    pending_checkins = todays_checkins - completed_checkins
    
    todays_checkouts = Reservation.objects.filter(check_out_date=today).count()
    completed_checkouts = CheckOut.objects.filter(check_out_time__date=today).count()
    pending_checkouts = todays_checkouts - completed_checkouts
    
    # Reservas pendentes para check-in/out
    pending_checkins_list = Reservation.objects.filter(
        check_in_date=today,
        status='confirmed'
    ).select_related('room')
    
    pending_checkouts_list = Reservation.objects.filter(
        check_out_date__lte=today,
        status='checked_in'
    ).select_related('room')
    
    # Atividades recentes (últimas 10)
    recent_activities = []
    
    # Adiciona check-ins recentes
    recent_checkins = CheckIn.objects.select_related(
        'reservation', 'reservation__room'
    ).order_by('-check_in_time')[:5]
    
    for checkin in recent_checkins:
        recent_activities.append({
            'timestamp': checkin.check_in_time,
            'description': f"Check-in: {checkin.reservation.guest_name} (Quarto {checkin.reservation.room.number})"
        })
    
    # Adiciona check-outs recentes
    recent_checkouts = CheckOut.objects.select_related(
        'reservation', 'reservation__room'
    ).order_by('-check_out_time')[:5]
    
    for checkout in recent_checkouts:
        recent_activities.append({
            'timestamp': checkout.check_out_time,
            'description': f"Check-out: {checkout.reservation.guest_name} (Quarto {checkout.reservation.room.number})"
        })
    
    # Ordena atividades por timestamp
    recent_activities.sort(key=lambda x: x['timestamp'], reverse=True)
    recent_activities = recent_activities[:10]
    
    # Quartos ocupados (reservas com status 'checked_in' e não checked_out)
    occupied_reservations = Reservation.objects.filter(status='checked_in', checked_out=False).select_related('room')
    context = {
        'occupancy_rate': occupancy_rate,
        'occupied_rooms': occupied_rooms,
        'available_rooms': total_rooms - occupied_rooms,
        'todays_checkins': todays_checkins,
        'completed_checkins': completed_checkins,
        'pending_checkins': pending_checkins,
        'todays_checkouts': todays_checkouts,
        'completed_checkouts': completed_checkouts,
        'pending_checkouts': pending_checkouts,
        'pending_checkins_list': pending_checkins_list,
        'pending_checkouts_list': pending_checkouts_list,
        'recent_activities': recent_activities,
        'occupied_reservations': occupied_reservations,
    }
    return render(request, 'home.html', context)