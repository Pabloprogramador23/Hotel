from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Prefetch, Sum
from django.http import HttpRequest, HttpResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .models import Reservation, ReservationGuest, Room


def _total_due(reservation: Reservation) -> Decimal:
    if not reservation:
        return Decimal('0')
    return (
        reservation.hospedes.aggregate(total=Sum('valor_devido'))['total']
        or Decimal('0')
    )


def _hydrate_rooms_with_reservations():
    active_reservations = Reservation.objects.ativas().prefetch_related('hospedes')
    rooms = list(
        Room.objects.all().prefetch_related(
            Prefetch('reservas', queryset=active_reservations, to_attr='reservas_ativas')
        )
    )

    for room in rooms:
        reservas = getattr(room, 'reservas_ativas', [])
        room.active_reservation = reservas[0] if reservas else None

    return rooms


@login_required
def dashboard(request: HttpRequest) -> HttpResponse:
    rooms = _hydrate_rooms_with_reservations()
    available_rooms = [room for room in rooms if room.active_reservation is None]

    today = timezone.localdate()

    pix_total = (
        ReservationGuest.objects.filter(
            pago=True,
            metodo_pagamento=ReservationGuest.MetodoPagamento.PIX,
            atualizado_em__date=today,
        ).aggregate(total=Sum('valor_devido'))['total']
        or Decimal('0')
    )
    cash_total = (
        ReservationGuest.objects.filter(
            pago=True,
            metodo_pagamento=ReservationGuest.MetodoPagamento.DINHEIRO,
            atualizado_em__date=today,
        ).aggregate(total=Sum('valor_devido'))['total']
        or Decimal('0')
    )

    context = {
        'rooms': rooms,
        'available_rooms': available_rooms,
        'totals': {
            'pix': pix_total,
            'dinheiro': cash_total,
        },
        'stats': {
            'ocupados': len(rooms) - len(available_rooms),
            'livres': len(available_rooms),
            'total': len(rooms),
        },
        'default_rate': Decimal('120.00'),
    }
    return render(request, 'reservations/dashboard.html', context)


@login_required
def room_detail(request: HttpRequest, room_id: int) -> HttpResponse:
    room = get_object_or_404(
        Room.objects.prefetch_related(
            Prefetch(
                'reservas',
                queryset=Reservation.objects.ativas().prefetch_related('hospedes'),
                to_attr='reservas_ativas',
            )
        ),
        pk=room_id,
    )
    reservas = getattr(room, 'reservas_ativas', [])
    reservation = reservas[0] if reservas else None
    total_due = _total_due(reservation)

    context = {
        'room': room,
        'reservation': reservation,
        'total_due': total_due,
        'available_rooms': list(
            Room.objects.filter(status=Room.Status.DISPONIVEL).order_by('numero')
        ),
        'default_rate': Decimal('120.00'),
        'form_errors': None,
        'form_data': None,
    }
    return render(request, 'reservations/room_detail.html', context)


@login_required
@require_POST
def quick_check_in(request: HttpRequest) -> HttpResponse:
    room_id = request.POST.get('room_id')
    guest_name = request.POST.get('guest_name', '').strip()
    raw_value = request.POST.get('valor_devido', '0').replace(',', '.')

    if not room_id or not guest_name:
        return HttpResponseBadRequest('Dados obrigatórios não informados.')

    room = get_object_or_404(Room, pk=room_id)

    if Reservation.objects.ativas().filter(room=room).exists():
        messages.error(request, 'O quarto já está ocupado neste momento.')
        return redirect('reservations:dashboard')

    try:
        amount = Decimal(raw_value)
    except (InvalidOperation, TypeError):
        amount = Decimal('0')

    with transaction.atomic():
        reservation = Reservation.objects.create(room=room)
        ReservationGuest.objects.create(
            reserva=reservation,
            nome=guest_name,
            valor_devido=amount,
            metodo_pagamento=ReservationGuest.MetodoPagamento.PENDENTE,
        )
        room.ocupar()

    return redirect('reservations:room_detail', room_id=room.id)


@login_required
@require_POST
def update_guest_payment(request: HttpRequest, guest_id: int) -> HttpResponse:
    guest = get_object_or_404(ReservationGuest, pk=guest_id)
    method = request.POST.get('method', ReservationGuest.MetodoPagamento.PENDENTE)

    valid_methods = {choice[0] for choice in ReservationGuest.MetodoPagamento.choices}
    if method not in valid_methods:
        method = ReservationGuest.MetodoPagamento.PENDENTE

    toggled_same_method = (
        guest.metodo_pagamento == method
        and guest.pago
        and method != ReservationGuest.MetodoPagamento.PENDENTE
    )

    if toggled_same_method:
        guest.metodo_pagamento = ReservationGuest.MetodoPagamento.PENDENTE
        guest.pago = False
    else:
        guest.metodo_pagamento = method
        guest.pago = method != ReservationGuest.MetodoPagamento.PENDENTE

    guest.save()

    response_context = {'guest': guest}

    if request.headers.get('Hx-Request', '').lower() == 'true':
        return render(request, 'reservations/partials/guest_row.html', response_context)

    return redirect('reservations:room_detail', room_id=guest.reserva.room_id)


@login_required
@require_POST
def add_guest(request: HttpRequest, reservation_id: int) -> HttpResponse:
    reservation = get_object_or_404(
        Reservation.objects.prefetch_related('hospedes', 'room'),
        pk=reservation_id,
    )

    name = request.POST.get('guest_name', '').strip()
    raw_value = (request.POST.get('valor_devido') or '').replace(',', '.')
    errors = {}

    if not name:
        errors['guest_name'] = 'Informe o nome do hóspede.'

    try:
        amount = Decimal(raw_value)
    except (InvalidOperation, TypeError):
        amount = None

    if amount is None or amount <= 0:
        errors['valor_devido'] = 'Informe um valor maior que zero.'

    if not reservation.ativa or reservation.data_saida is not None:
        errors['reservation'] = 'Não é possível adicionar hóspedes em reservas encerradas.'

    if not errors:
        ReservationGuest.objects.create(
            reserva=reservation,
            nome=name,
            valor_devido=amount,
            metodo_pagamento=ReservationGuest.MetodoPagamento.PENDENTE,
        )

        reservation = Reservation.objects.prefetch_related('hospedes', 'room').get(pk=reservation.pk)

    context = {
        'reservation': reservation,
        'room': reservation.room,
        'total_due': _total_due(reservation),
        'form_errors': errors if errors else None,
        'form_data': {
            'guest_name': name,
            'valor_devido': request.POST.get('valor_devido', ''),
        } if errors else None,
    }

    template = 'reservations/partials/guest_section.html'

    if request.headers.get('Hx-Request', '').lower() == 'true':
        status = 400 if errors else 200
        response = render(request, template, context)
        response.status_code = status
        return response

    if errors:
        messages.error(request, 'Não foi possível adicionar o hóspede. Verifique os dados informados.')
    else:
        messages.success(request, 'Hóspede adicionado com sucesso.')
    return redirect('reservations:room_detail', room_id=reservation.room_id)
