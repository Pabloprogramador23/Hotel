import os
import sys
from datetime import timedelta
from decimal import Decimal

import django
from django.utils import timezone

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hotel_hms.settings')
django.setup()

from django.contrib.auth import get_user_model
from apps.reservations.models import Reservation, ReservationGuest, Room
from apps.finance.models import Expense, ExtraIncome, LedgerAdjustment

User = get_user_model()


def _reset_data():
    print('🧹 Limpando registros antigos...')
    ReservationGuest.objects.all().delete()
    LedgerAdjustment.objects.all().delete()
    Expense.objects.all().delete()
    ExtraIncome.objects.all().delete()
    Reservation.objects.all().delete()
    Room.objects.all().delete()


def _ensure_admin():
    if not User.objects.filter(username='admin').exists():
        User.objects.create_superuser('admin', 'admin@example.com', 'admin')
        print("👤 Superusuário 'admin' criado (senha: admin)")


def _create_rooms():
    print('🛏️ Criando quartos de exemplo...')
    rooms = []
    for numero in ['101', '102', '103', '201', '202', '301']:
        rooms.append(Room.objects.create(numero=numero, status=Room.Status.DISPONIVEL))
    return rooms


def _create_reservations(rooms):
    print('📅 Criando reservas e hóspedes...')
    agora = timezone.now()

    reserva_ativa = Reservation.objects.create(room=rooms[0])
    ReservationGuest.objects.create(
        reserva=reserva_ativa,
        nome='Ana Souza',
        valor_devido=Decimal('180.00'),
        pago=False,
        metodo_pagamento=ReservationGuest.MetodoPagamento.PENDENTE,
    )

    reserva_ativa.hospedes.create(
        nome='Bruno Souza',
        valor_devido=Decimal('150.00'),
        pago=True,
        metodo_pagamento=ReservationGuest.MetodoPagamento.PIX,
    )

    reserva_encerrada = Reservation.objects.create(room=rooms[1])
    reserva_encerrada.encerrar(agora - timedelta(hours=6))
    ReservationGuest.objects.create(
        reserva=reserva_encerrada,
        nome='Carla Lima',
        valor_devido=Decimal('220.00'),
        pago=True,
        metodo_pagamento=ReservationGuest.MetodoPagamento.DINHEIRO,
    )

    reserva_pendente = Reservation.objects.create(room=rooms[2])
    reserva_pendente.hospedes.create(
        nome='Daniel Pereira',
        valor_devido=Decimal('95.00'),
        pago=False,
        metodo_pagamento=ReservationGuest.MetodoPagamento.PENDENTE,
    )

    return reserva_ativa, reserva_encerrada, reserva_pendente


def _create_finance_entries(reserva):
    print('💰 Criando registros financeiros...')
    today = timezone.localdate()

    Expense.objects.create(
        description='Conta de energia',
        amount=Decimal('320.00'),
        category='utilities',
        payment_date=today,
        payment_method='PIX',
        notes='Fatura mensal da concessionária',
    )

    Expense.objects.create(
        description='Compra de enxoval',
        amount=Decimal('210.00'),
        category='supplies',
        payment_date=today - timedelta(days=1),
        payment_method='Cartão',
        notes='Lençóis e toalhas novas',
    )

    ExtraIncome.objects.create(
        description='Reserva de auditório',
        amount=Decimal('500.00'),
        received_date=today,
        method='Transferência',
        notes='Evento corporativo',
    )

    LedgerAdjustment.objects.create(
        reservation=reserva,
        descricao='Consumo frigobar',
        tipo=LedgerAdjustment.Tipo.CREDITO,
        valor=Decimal('65.00'),
        metodo='Interno',
    )

    LedgerAdjustment.objects.create(
        descricao='Correção de caixa',
        tipo=LedgerAdjustment.Tipo.DEBITO,
        valor=Decimal('30.00'),
        metodo='PIX',
    )


def seed():
    _reset_data()
    _ensure_admin()
    rooms = _create_rooms()
    reserva_ativa, _, _ = _create_reservations(rooms)
    _create_finance_entries(reserva_ativa)
    print('✅ Base de dados populada com sucesso!')


if __name__ == '__main__':
    seed()
