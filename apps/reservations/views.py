from django.shortcuts import render
from django.db.models import Q
from datetime import datetime
from .models import Reservation
from apps.rooms.models import Room

def reservation_list(request):
    # Inicializa a queryset
    reservations = Reservation.objects.all().select_related('room')
    
    # Aplicar filtros
    date_filter = request.GET.get('date')
    status_filter = request.GET.get('status')
    guest_filter = request.GET.get('guest')
    
    if date_filter:
        date = datetime.strptime(date_filter, '%Y-%m-%d').date()
        reservations = reservations.filter(
            Q(check_in_date=date) | Q(check_out_date=date)
        )
    
    if status_filter:
        reservations = reservations.filter(status=status_filter)
    
    if guest_filter:
        reservations = reservations.filter(
            guest_name__icontains=guest_filter
        )
    
    context = {
        'reservations': reservations,
        'rooms': Room.objects.all()  # Para o select de quartos no formulário
    }
    
    return render(request, 'reservations/list.html', context)
