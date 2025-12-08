"""Testes de integração cobrindo o fluxo básico de reservas e pagamentos."""

import pytest
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.urls import reverse

from apps.checkin_checkout.models import CheckIn, CheckOut
from apps.reservations.models import Reservation, ReservationGuest, Room


@pytest.mark.django_db
class TestFullGuestJourney:
    """Valida o fluxo completo de reserva, check-in, pagamento e check-out."""

    @pytest.fixture
    def room(self):
        return Room.objects.create(numero="801")

    def test_complete_guest_journey(self, room):
        reservation = Reservation.objects.create(room=room)
        assert reservation.room == room
        room.refresh_from_db()
        assert room.status == Room.Status.OCUPADO

        check_in = CheckIn.objects.create(reservation=reservation, document_scanned=True)
        assert check_in.document_scanned is True

        ReservationGuest.objects.create(
            reserva=reservation,
            nome="Hóspede Pago",
            valor_devido=Decimal('150.00'),
            pago=True,
            metodo_pagamento=ReservationGuest.MetodoPagamento.PIX,
        )
        pending_guest = ReservationGuest.objects.create(
            reserva=reservation,
            nome="Hóspede Pendente",
            valor_devido=Decimal('80.00'),
            pago=False,
            metodo_pagamento=ReservationGuest.MetodoPagamento.PENDENTE,
        )

        with pytest.raises(ValidationError):
            CheckOut.objects.create(reservation=reservation, check_in=check_in)

        pending_guest.registrar_pagamento(ReservationGuest.MetodoPagamento.DINHEIRO)
        checkout = CheckOut.objects.create(reservation=reservation, check_in=check_in)

        reservation.refresh_from_db()
        room.refresh_from_db()
        assert reservation.ativa is False
        assert room.status == Room.Status.DISPONIVEL
        assert checkout.has_pending_payments is False


@pytest.mark.django_db
class TestReservationPaymentFlow:
    """Garante que a view de atualização de pagamento integra corretamente com o modelo."""

    def test_update_guest_payment_toggle(self, client):
        room = Room.objects.create(numero="901")
        reservation = Reservation.objects.create(room=room)
        guest = ReservationGuest.objects.create(
            reserva=reservation,
            nome="Visitante",
            valor_devido=Decimal('90.00'),
            pago=False,
        )

        url = reverse('reservations:update_guest_payment', args=[guest.id])

        response = client.post(url, data={'method': ReservationGuest.MetodoPagamento.PIX})
        assert response.status_code == 302
        guest.refresh_from_db()
        assert guest.pago is True
        assert guest.metodo_pagamento == ReservationGuest.MetodoPagamento.PIX

        response = client.post(url, data={'method': ReservationGuest.MetodoPagamento.PIX})
        assert response.status_code == 302
        guest.refresh_from_db()
        assert guest.pago is False
        assert guest.metodo_pagamento == ReservationGuest.MetodoPagamento.PENDENTE
