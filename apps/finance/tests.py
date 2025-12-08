import pytest
from decimal import Decimal
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.finance.models import Expense, ExtraIncome, LedgerAdjustment
from apps.reservations.models import Reservation, ReservationGuest, Room


@pytest.fixture
def user(db):
    User = get_user_model()
    return User.objects.create_user(username='tester', password='strong-pass')


@pytest.fixture
def reservation(db):
    room = Room.objects.create(numero='301')
    return Reservation.objects.create(room=room)


@pytest.mark.django_db
def test_cash_overview_returns_daily_totals(client, user, reservation):
    client.force_login(user)
    today = timezone.localdate()

    reservation.hospedes.create(
        nome='Ana',
        valor_devido=Decimal('120.00'),
        pago=True,
        metodo_pagamento=ReservationGuest.MetodoPagamento.PIX,
    )

    reservation.hospedes.create(
        nome='Bruno',
        valor_devido=Decimal('80.00'),
        pago=True,
        metodo_pagamento=ReservationGuest.MetodoPagamento.DINHEIRO,
    )

    LedgerAdjustment.objects.create(
        reservation=reservation,
        descricao='Consumo frigobar',
        tipo=LedgerAdjustment.Tipo.CREDITO,
        valor=Decimal('25.00'),
        metodo='PIX',
    )

    LedgerAdjustment.objects.create(
        descricao='Acerto de caixa',
        tipo=LedgerAdjustment.Tipo.DEBITO,
        valor=Decimal('10.00'),
        metodo='Dinheiro',
    )

    ExtraIncome.objects.create(
        description='Locação salão',
        amount=Decimal('200.00'),
        received_date=today,
        method='Transferência',
    )

    Expense.objects.create(
        description='Compra de amenities',
        amount=Decimal('90.00'),
        category='supplies',
        payment_date=today,
        payment_method='PIX',
    )

    response = client.get(reverse('finance:cash_overview'))
    assert response.status_code == 200
    payload = response.json()

    assert payload['pix'] == 120.0
    assert payload['dinheiro'] == 80.0
    assert payload['ajustes_credito'] == 25.0
    assert payload['ajustes_debito'] == 10.0
    assert payload['extras'] == 200.0
    assert payload['despesas'] == 90.0


@pytest.mark.django_db
def test_reservation_balances_endpoint_groups_pending_amounts(client, user, reservation):
    client.force_login(user)

    reservation.hospedes.create(
        nome='Convidado Pago',
        valor_devido=Decimal('150.00'),
        pago=True,
        metodo_pagamento=ReservationGuest.MetodoPagamento.PIX,
    )

    reservation.hospedes.create(
        nome='Convidado Pendente',
        valor_devido=Decimal('60.00'),
        pago=False,
        metodo_pagamento=ReservationGuest.MetodoPagamento.PENDENTE,
    )

    response = client.get(reverse('finance:reservation_balances'))
    assert response.status_code == 200
    reservations = response.json()['reservations']
    assert len(reservations) == 1
    entry = reservations[0]
    assert entry['total'] == 210.0
    assert entry['paid'] == 150.0
    assert entry['pending'] == 60.0
    assert entry['active'] is True


@pytest.mark.django_db
def test_create_adjustment_endpoint_creates_record(client, user, reservation):
    client.force_login(user)
    payload = {
        'tipo': LedgerAdjustment.Tipo.CREDITO,
        'descricao': 'Reajuste manual',
        'valor': '45.00',
        'metodo': 'Dinheiro',
        'reservation_id': reservation.id,
    }

    response = client.post(reverse('finance:create_adjustment'), data=payload)
    assert response.status_code == 200
    assert LedgerAdjustment.objects.filter(descricao='Reajuste manual').exists()
