from django.shortcuts import render
from .models import Room, MaintenanceRecord

def room_list(request):
    # Inicializa a queryset
    rooms = Room.objects.all()
    
    # Aplicar filtros
    room_type = request.GET.get('type')
    status = request.GET.get('status')
    
    if room_type:
        rooms = rooms.filter(room_type=room_type)
    if status:
        rooms = rooms.filter(status=status)
    
    # Adiciona o histórico de manutenção para cada quarto
    for room in rooms:
        room.maintenance_history = MaintenanceRecord.objects.filter(room=room).order_by('-date')[:5]
    
    context = {
        'rooms': rooms,
    }
    
    return render(request, 'rooms/list.html', context)
