from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_POST

from apps.checkin_checkout.models import CheckIn, CheckOut
from apps.reservations.models import Reservation, ReservationGuest, Room

@login_required
@require_POST
def perform_checkin(request, reservation_id):
    """
    Realiza o check-in de uma reserva
    """
    try:
        with transaction.atomic():
            reservation = get_object_or_404(Reservation, id=reservation_id)

            if reservation.ocupando:
                return JsonResponse({
                    'success': False,
                    'message': 'Esta reserva já está ativa.'
                }, status=400)

            if reservation.room.status != Room.Status.DISPONIVEL:
                return JsonResponse({
                    'success': False,
                    'message': f"O quarto {reservation.room.numero} não está disponível."
                }, status=400)

            checkin, created = CheckIn.objects.get_or_create(
                reservation=reservation,
                defaults={'document_scanned': True, 'completed': True}
            )

            if not created:
                return JsonResponse({
                    'success': False,
                    'message': 'Já existe um registro de check-in para esta reserva.'
                }, status=400)

            return JsonResponse({
                'success': True,
                'message': 'Check-in registrado com sucesso.',
                'room': reservation.room.numero,
                'started_at': checkin.started_at.isoformat()
            })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Ocorreu um erro ao processar o check-in: {str(e)}'
        }, status=500)

@login_required
@require_POST
def perform_checkout(request, reservation_id):
    """
    Realiza o check-out de uma reserva
    """
    try:
        with transaction.atomic():
            reservation = get_object_or_404(Reservation, id=reservation_id)

            if not reservation.ocupando:
                return JsonResponse({
                    'success': False,
                    'message': 'Esta reserva já está encerrada.'
                }, status=400)

            has_pending = reservation.hospedes.filter(pago=False).exists()
            if has_pending:
                return JsonResponse({
                    'success': False,
                    'message': 'Existem hóspedes com valores pendentes.'
                }, status=400)

            checkin = CheckIn.objects.filter(reservation=reservation).first()

            checkout, created = CheckOut.objects.get_or_create(
                reservation=reservation,
                defaults={'check_in': checkin, 'has_pending_payments': False, 'completed': True}
            )

            if not created:
                return JsonResponse({
                    'success': False,
                    'message': 'Já existe um check-out para esta reserva.'
                }, status=400)

            return JsonResponse({
                'success': True,
                'message': 'Check-out registrado com sucesso.',
                'finished_at': checkout.finished_at.isoformat()
            })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Ocorreu um erro ao processar o check-out: {str(e)}'
        }, status=500)

@login_required
def list_current_guests(request):
    """
    Lista todas as reservas com check-in mas sem check-out
    """
    current_guests = Reservation.objects.ativas().select_related('room').prefetch_related('hospedes')

    guests_data = [{
        'id': reservation.id,
        'room_number': reservation.room.numero,
        'guests': [guest.nome for guest in reservation.hospedes.all()],
        'check_in_time': reservation.data_entrada.strftime('%Y-%m-%d %H:%M:%S')
    } for reservation in current_guests]

    return JsonResponse({'current_guests': guests_data})

@login_required
def list_expected_arrivals(request):
    """
    Lista todas as reservas que têm check-in esperado para hoje
    """
    available_rooms = Room.objects.filter(status=Room.Status.DISPONIVEL).order_by('numero')

    arrivals_data = [{
        'room_id': room.id,
        'room_number': room.numero
    } for room in available_rooms]

    return JsonResponse({'available_rooms': arrivals_data})

@login_required
def list_expected_departures(request):
    """
    Lista todas as reservas que têm check-out esperado para hoje ou datas anteriores (atrasadas)
    """
    today = timezone.localdate()
    active_reservations = Reservation.objects.ativas().select_related('room')
    departures = active_reservations.filter(data_entrada__date__lt=today)

    departures_data = [{
        'id': reservation.id,
        'room_number': reservation.room.numero,
        'guests': [guest.nome for guest in reservation.hospedes.all()],
        'started_at': reservation.data_entrada.strftime('%Y-%m-%d %H:%M:%S')
    } for reservation in departures]

    return JsonResponse({'expected_departures': departures_data})
