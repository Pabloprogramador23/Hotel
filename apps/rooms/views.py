from django.core.paginator import Paginator
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from .models import Room, MaintenanceRecord

def room_list(request: HttpRequest) -> HttpResponse:
    """
    Exibe a lista de quartos com filtros e paginação.

    Args:
        request (HttpRequest): Requisição HTTP.

    Returns:
        HttpResponse: Página de listagem de quartos.
    """
    # Inicializa a queryset
    rooms = Room.objects.all().prefetch_related('maintenance_records')
    
    # Aplicar filtros
    room_type = request.GET.get('type')
    status = request.GET.get('status')
    
    if room_type:
        rooms = rooms.filter(room_type=room_type)
    if status:
        rooms = rooms.filter(status=status)
    
    # Adiciona o histórico de manutenção para cada quarto
    for room in rooms:
        room.maintenance_history = room.maintenance_records.order_by('-date')[:5]
    # Paginação
    paginator = Paginator(rooms, 20)  # 20 por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'rooms': page_obj.object_list,
        'page_obj': page_obj,
    }
    return render(request, 'rooms/list.html', context)
