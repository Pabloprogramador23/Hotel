from django.shortcuts import render
from django.db.models import Count
from datetime import date
from apps.rooms.models import Room
from apps.checkin_checkout.models import CheckIn
from apps.reservations.models import Reservation

def report_list(request):
    return render(request, 'reports/list.html', {
        'title': 'Reports',
        'reports': [
            {'name': 'Occupancy Report', 'url': 'reports:occupancy'},
            {'name': 'Revenue Report', 'url': 'reports:revenue'},
            {'name': 'Check-ins Report', 'url': 'reports:checkins'},
        ]
    })

def occupancy_report(request):
    total_rooms = Room.objects.count()
    occupied_rooms = Room.objects.filter(status='occupied').count()
    occupancy_rate = (occupied_rooms / total_rooms * 100) if total_rooms > 0 else 0
    
    context = {
        'total_rooms': total_rooms,
        'occupied_rooms': occupied_rooms,
        'occupancy_rate': round(occupancy_rate, 2)
    }
    return render(request, 'reports/occupancy.html', context)

def revenue_report(request):
    start_date = request.GET.get('start_date', date.today())
    end_date = request.GET.get('end_date', date.today())
    
    context = {
        'start_date': start_date,
        'end_date': end_date,
        'revenue_data': []  # To be implemented with actual revenue calculations
    }
    return render(request, 'reports/revenue.html', context)

def checkins_report(request):
    checkins = CheckIn.objects.select_related('reservation').order_by('-check_in_time')
    
    context = {
        'checkins': checkins
    }
    return render(request, 'reports/checkins.html', context)
