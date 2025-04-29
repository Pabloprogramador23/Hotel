from django.http import JsonResponse
from django.db.models import Count, Q
from datetime import date, datetime, timedelta
from apps.rooms.models import Room
from apps.reservations.models import Reservation
from apps.checkin_checkout.models import CheckIn, CheckOut
import json
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth.decorators import user_passes_test

def dashboard_stats(request):
    today = date.today()
    
    # Estatísticas de ocupação
    total_rooms = Room.objects.count()
    occupied_rooms = Room.objects.filter(status='occupied').count()
    occupancy_rate = round((occupied_rooms / total_rooms * 100) if total_rooms > 0 else 0, 1)
    
    # Estatísticas de check-in/out
    todays_checkins = Reservation.objects.filter(check_in_date=today).count()
    
    # Usar datetime para filtrar por data de hoje
    today_start = datetime.combine(today, datetime.min.time())
    today_end = datetime.combine(today, datetime.max.time())
    
    completed_checkins = CheckIn.objects.filter(
        check_in_time__range=(today_start, today_end)
    ).count()
    
    pending_checkins = todays_checkins - completed_checkins
    
    todays_checkouts = Reservation.objects.filter(check_out_date=today).count()
    completed_checkouts = CheckOut.objects.filter(
        check_out_time__range=(today_start, today_end)
    ).count()
    
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

def available_rooms(request):
    """API para buscar quartos disponíveis conforme tipo e datas"""
    # Obter parâmetros da requisição
    room_type = request.GET.get('room_type')
    check_in = request.GET.get('check_in', date.today().isoformat())
    check_out = request.GET.get('check_out', (date.today() + timedelta(days=1)).isoformat())
    
    try:
        check_in_date = datetime.strptime(check_in, '%Y-%m-%d').date()
        check_out_date = datetime.strptime(check_out, '%Y-%m-%d').date()
    except ValueError:
        return JsonResponse({'error': 'Formato de data inválido'}, status=400)
    
    # Filtrar quartos por tipo (se especificado)
    rooms = Room.objects.all()
    if room_type and room_type != 'all':
        rooms = rooms.filter(room_type=room_type)
    
    # Excluir quartos que já têm reservas sobrepostas
    unavailable_rooms = Reservation.objects.filter(
        check_in_date__lt=check_out_date,
        check_out_date__gt=check_in_date,
        status__in=['pending', 'confirmed', 'checked_in']
    ).values_list('room_id', flat=True)
    
    available_rooms = rooms.exclude(id__in=unavailable_rooms)
    
    # Formatando a resposta
    rooms_data = [
        {
            'id': room.id,
            'number': room.number,
            'room_type': room.room_type,
            'status': room.status,
            'description': room.description
        }
        for room in available_rooms
    ]
    
    return JsonResponse(rooms_data, safe=False)

@require_http_methods(["POST"])
@csrf_protect
@user_passes_test(lambda u: u.is_superuser, login_url='/admin/login/')
def reservation_create(request):
    """API para criar uma nova reserva (apenas superusuários)"""
    try:
        data = json.loads(request.body)

        # Validar dados obrigatórios
        required_fields = ['guest_name', 'guest_email', 'room_id', 'check_in_date', 'check_out_date']
        for field in required_fields:
            if field not in data:
                return JsonResponse({'message': f'Campo obrigatório ausente: {field}'}, status=400)

        # Validar datas
        try:
            check_in_date = datetime.strptime(data['check_in_date'], '%Y-%m-%d').date()
            check_out_date = datetime.strptime(data['check_out_date'], '%Y-%m-%d').date()
            if check_out_date <= check_in_date:
                return JsonResponse({'message': 'A data de check-out deve ser posterior à data de check-in'}, status=400)
        except ValueError:
            return JsonResponse({'message': 'Formato de data inválido. Use YYYY-MM-DD.'}, status=400)

        # Obter o quarto
        try:
            room = Room.objects.get(id=data['room_id'])
        except Room.DoesNotExist:
            return JsonResponse({'message': 'Quarto não encontrado'}, status=404)

        # Criar a reserva
        reservation = Reservation(
            guest_name=data['guest_name'],
            guest_email=data['guest_email'],
            room=room,
            check_in_date=check_in_date,
            check_out_date=check_out_date,
            notes=data.get('notes', ''),
            status=data.get('status', 'confirmed')
        )

        # Tentar salvar (a validação acontece no método save)
        try:
            reservation.save()
            return JsonResponse({'id': reservation.id, 'message': 'Reserva criada com sucesso'})
        except ValueError as e:
            return JsonResponse({'message': str(e)}, status=400)

    except json.JSONDecodeError:
        return JsonResponse({'message': 'Dados JSON inválidos'}, status=400)
    except Exception as e:
        return JsonResponse({'message': f'Erro ao criar reserva: {str(e)}'}, status=500)
