from django.shortcuts import render
from django.db.models import Count, Q, Sum
from django.db.models.functions import TruncDate
from datetime import date, timedelta, datetime
from apps.rooms.models import Room
from apps.checkin_checkout.models import CheckIn
from apps.reservations.models import Reservation
from apps.finance.models import Invoice

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
    # Cálculos básicos de ocupação
    total_rooms = Room.objects.count()
    occupied_rooms = Room.objects.filter(status='occupied').count()
    occupancy_rate = (occupied_rooms / total_rooms * 100) if total_rooms > 0 else 0
    
    # Ocupação por tipo de quarto
    room_type_stats = (
        Room.objects.values('room_type')
        .annotate(
            total=Count('id'),
            occupied=Count('id', filter=Q(status='occupied'))
        )
        .order_by('room_type')
    )

    # Tendência de ocupação dos últimos 7 dias
    end_date = date.today()
    start_date = end_date - timedelta(days=6)
    occupancy_trend = []
    
    for single_date in (start_date + timedelta(n) for n in range(7)):
        checkins = CheckIn.objects.filter(check_in_time__date=single_date).count()
        occupancy_trend.append({
            'date': single_date,
            'checkins': checkins
        })
    
    context = {
        'total_rooms': total_rooms,
        'occupied_rooms': occupied_rooms,
        'occupancy_rate': round(occupancy_rate, 2),
        'room_type_stats': room_type_stats,
        'occupancy_trend': occupancy_trend
    }
    return render(request, 'reports/occupancy.html', context)

def revenue_report(request):
    today = date.today()
    start_date = today
    end_date = today

    # Só usar datas do request se ambas start_date e end_date estiverem presentes e forem válidas
    if all(param in request.GET for param in ['start_date', 'end_date']):
        try:
            start_date = datetime.strptime(request.GET['start_date'], '%Y-%m-%d').date()
            end_date = datetime.strptime(request.GET['end_date'], '%Y-%m-%d').date()
        except (TypeError, ValueError):
            pass  # Manter as datas padrão (hoje) se o parsing falhar
    
    # Buscar dados de receita do período especificado
    query = Invoice.objects
    if start_date == end_date:
        # Se for um único dia, usar filtro exato
        query = query.filter(issued_at__date=start_date)
    else:
        # Se for um período, usar range de datas
        query = query.filter(issued_at__date__gte=start_date, issued_at__date__lte=end_date)
    
    revenue_data = (
        query
        .values('issued_at__date')
        .annotate(
            date=TruncDate('issued_at'),
            total_amount=Sum('amount'),
            paid_amount=Sum('amount', filter=Q(paid=True)),
            pending_amount=Sum('amount', filter=Q(paid=False))
        )
        .order_by('issued_at__date')
    )
    
    # Calcular totais do período
    total_revenue = sum(day['total_amount'] or 0 for day in revenue_data)
    total_paid = sum(day['paid_amount'] or 0 for day in revenue_data)
    total_pending = sum(day['pending_amount'] or 0 for day in revenue_data)
    
    context = {
        'start_date': start_date,
        'end_date': end_date,
        'revenue_data': revenue_data,
        'total_revenue': total_revenue,
        'total_paid': total_paid,
        'total_pending': total_pending
    }
    return render(request, 'reports/revenue.html', context)

def checkins_report(request):
    checkins = CheckIn.objects.select_related('reservation').order_by('-check_in_time')
    
    context = {
        'checkins': checkins
    }
    return render(request, 'reports/checkins.html', context)
