from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.db.models import Q
from django.core.paginator import Paginator
from django.core.cache import cache
from datetime import datetime
from .models import Reservation
from apps.rooms.models import Room

def reservation_list(request: HttpRequest) -> HttpResponse:
    """
    Exibe a lista de reservas com filtros e paginação.

    Args:
        request (HttpRequest): Requisição HTTP.

    Returns:
        HttpResponse: Página de listagem de reservas.
    """
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
    # Paginação
    paginator = Paginator(reservations, 20)  # 20 por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    # Cache para lista de quartos
    rooms = cache.get('rooms_list')
    if rooms is None:
        rooms = list(Room.objects.all())
        cache.set('rooms_list', rooms, 600)  # 10 minutos
    context = {
        'reservations': page_obj.object_list,
        'page_obj': page_obj,
        'rooms': rooms  # Para o select de quartos no formulário
    }
    return render(request, 'reservations/list.html', context)
