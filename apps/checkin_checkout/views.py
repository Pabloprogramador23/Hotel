from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db import transaction
from django.utils import timezone

from apps.reservations.models import Reservation
from apps.finance.models import Invoice
from apps.rooms.models import Room
from apps.checkin_checkout.models import CheckIn, CheckOut

@require_POST
def perform_checkin(request, reservation_id):
    """
    Realiza o check-in de uma reserva
    """
    try:
        with transaction.atomic():
            reservation = get_object_or_404(Reservation, id=reservation_id)
            
            # Verificar se a reserva já tem check-in
            if reservation.checked_in:
                return JsonResponse({
                    'success': False,
                    'message': 'Esta reserva já possui check-in'
                }, status=400)
            
            # Verificar se a reserva está dentro da data prevista
            today = timezone.now().date()
            if reservation.check_in_date > today:
                return JsonResponse({
                    'success': False, 
                    'message': 'Não é possível fazer check-in antes da data de início da reserva'
                }, status=400)
            
            # Verificar se o quarto está disponível
            room = reservation.room
            if room.status != 'available' and room.status != 'reserved' and room.status != 'clean':
                return JsonResponse({
                    'success': False,
                    'message': f'O quarto {room.number} não está disponível para check-in. Status atual: {room.status}'
                }, status=400)
            
            # Criar o objeto CheckIn
            checkin = CheckIn(
                reservation=reservation,
                document_scanned=True,  # Valor padrão, ajuste conforme necessário
                completed=True
            )
            
            # O salvamento do CheckIn irá atualizar automaticamente a reserva e o status dela
            checkin.save()
            
            # Atualizar o status do quarto
            room.status = 'occupied'
            room.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Check-in realizado com sucesso',
                'check_in_time': reservation.check_in_time.strftime('%Y-%m-%d %H:%M:%S') if reservation.check_in_time else None
            })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Ocorreu um erro ao processar o check-in: {str(e)}'
        }, status=500)

@require_POST
def perform_checkout(request, reservation_id):
    """
    Realiza o check-out de uma reserva
    """
    try:
        with transaction.atomic():
            reservation = get_object_or_404(Reservation, id=reservation_id)
            
            # Verificar se a reserva tem check-in
            if not reservation.checked_in:
                return JsonResponse({
                    'success': False,
                    'message': 'Esta reserva não possui check-in'
                }, status=400)
                
            # Verificar se a reserva já tem check-out
            if reservation.checked_out:
                return JsonResponse({
                    'success': False,
                    'message': 'Esta reserva já possui check-out'
                }, status=400)
            
            # Verificar se todas as faturas estão pagas
            unpaid_invoices = Invoice.objects.filter(reservation=reservation, paid=False).count()
            if unpaid_invoices > 0:
                return JsonResponse({
                    'success': False,
                    'message': f'Existem {unpaid_invoices} faturas pendentes. Todas as faturas devem ser pagas antes do check-out'
                }, status=400)
            
            # Buscar o check-in relacionado
            try:
                checkin = CheckIn.objects.get(reservation=reservation)
            except CheckIn.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'message': 'O registro de check-in não foi encontrado'
                }, status=400)
                
            # Criar o objeto CheckOut
            checkout = CheckOut(
                reservation=reservation,
                check_in=checkin,
                has_pending_payments=False,  # Já verificamos acima que não há faturas pendentes
                completed=True
            )
            
            # O salvamento do CheckOut irá atualizar automaticamente a reserva e o status dela
            checkout.save()
            
            # Atualizar o status do quarto
            room = reservation.room
            room.status = 'needs_cleaning'
            room.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Check-out realizado com sucesso',
                'check_out_time': reservation.check_out_time.strftime('%Y-%m-%d %H:%M:%S') if reservation.check_out_time else None
            })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Ocorreu um erro ao processar o check-out: {str(e)}'
        }, status=500)

def list_current_guests(request):
    """
    Lista todas as reservas com check-in mas sem check-out
    """
    current_guests = Reservation.objects.filter(checked_in=True, checked_out=False)
    
    guests_data = [{
        'id': reservation.id,
        'guest_name': reservation.guest_name,
        'room_number': reservation.room.number,
        'check_in_time': reservation.check_in_time.strftime('%Y-%m-%d %H:%M:%S') if reservation.check_in_time else None,
        'expected_checkout': reservation.check_out_date.strftime('%Y-%m-%d')
    } for reservation in current_guests]
    
    return JsonResponse({'current_guests': guests_data})

def list_expected_arrivals(request):
    """
    Lista todas as reservas que têm check-in esperado para hoje
    """
    today = timezone.now().date()
    expected_arrivals = Reservation.objects.filter(check_in_date=today, checked_in=False)
    
    arrivals_data = [{
        'id': reservation.id,
        'guest_name': reservation.guest_name,
        'room_number': reservation.room.number,
        'expected_checkin': reservation.check_in_date.strftime('%Y-%m-%d')
    } for reservation in expected_arrivals]
    
    return JsonResponse({'expected_arrivals': arrivals_data})

def list_expected_departures(request):
    """
    Lista todas as reservas que têm check-out esperado para hoje
    """
    today = timezone.now().date()
    expected_departures = Reservation.objects.filter(check_out_date=today, checked_in=True, checked_out=False)
    
    departures_data = [{
        'id': reservation.id,
        'guest_name': reservation.guest_name,
        'room_number': reservation.room.number,
        'check_in_time': reservation.check_in_time.strftime('%Y-%m-%d %H:%M:%S') if reservation.check_in_time else None,
        'expected_checkout': reservation.check_out_date.strftime('%Y-%m-%d')
    } for reservation in expected_departures]
    
    return JsonResponse({'expected_departures': departures_data})
