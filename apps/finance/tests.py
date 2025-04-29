import pytest
from decimal import Decimal
from datetime import date, timedelta

from apps.finance.models import Invoice
from apps.reservations.models import Reservation
from apps.rooms.models import Room


@pytest.mark.django_db
class TestInvoiceModel:
    """Testes para o modelo Invoice"""
    
    @pytest.fixture
    def setup_reservation(self):
        """Fixture para criar quarto e reserva para testes"""
        room = Room.objects.create(
            number="601",
            room_type="double",
            status="clean"
        )
        
        check_in_date = date.today()
        check_out_date = check_in_date + timedelta(days=3)
        
        reservation = Reservation.objects.create(
            guest_name="Invoice Test Guest",
            room=room,
            check_in_date=check_in_date,
            check_out_date=check_out_date,
            status="confirmed"
        )
        
        return reservation
    
    def test_create_invoice(self, setup_reservation):
        """Teste para criação básica de uma fatura"""
        invoice = Invoice.objects.create(
            reservation=setup_reservation,
            amount=Decimal('150.00'),
            paid=False
        )
        
        assert invoice.reservation == setup_reservation
        assert invoice.amount == Decimal('150.00')
        assert invoice.paid is False
        assert invoice.issued_at is not None
        assert str(invoice) == f"Invoice {invoice.id} - Reservation {setup_reservation.id}"
    
    def test_update_payment_status(self, setup_reservation):
        """Teste para atualização do status de pagamento de uma fatura"""
        invoice = Invoice.objects.create(
            reservation=setup_reservation,
            amount=Decimal('200.00'),
            paid=False
        )
        
        # Verificar status inicial
        assert invoice.paid is False
        
        # Atualizar status de pagamento
        invoice.paid = True
        invoice.save()
        
        # Recuperar fatura atualizada do banco
        updated_invoice = Invoice.objects.get(id=invoice.id)
        assert updated_invoice.paid is True
    
    def test_multiple_invoices_for_reservation(self, setup_reservation):
        """Teste para múltiplas faturas associadas a uma única reserva"""
        # Criar várias faturas para a mesma reserva
        invoice1 = Invoice.objects.create(
            reservation=setup_reservation,
            amount=Decimal('100.00'),
            paid=True
        )
        
        invoice2 = Invoice.objects.create(
            reservation=setup_reservation,
            amount=Decimal('50.00'),
            paid=False
        )
        
        invoice3 = Invoice.objects.create(
            reservation=setup_reservation,
            amount=Decimal('75.00'),
            paid=True
        )
        
        # Verificar que todas as faturas foram criadas
        assert Invoice.objects.count() == 3
        
        # Verificar que a reserva possui as faturas relacionadas
        reservation_invoices = setup_reservation.invoices.all()
        assert reservation_invoices.count() == 3
        assert invoice1 in reservation_invoices
        assert invoice2 in reservation_invoices
        assert invoice3 in reservation_invoices
        
        # Verificar total de faturas pagas e não pagas
        assert reservation_invoices.filter(paid=True).count() == 2
        assert reservation_invoices.filter(paid=False).count() == 1
        
        # Calcular soma total das faturas
        total_amount = sum(invoice.amount for invoice in reservation_invoices)
        assert total_amount == Decimal('225.00')
    
    def test_cascade_delete(self, setup_reservation):
        """Teste para garantir que faturas são excluídas quando a reserva é removida"""
        # Criar faturas
        Invoice.objects.create(
            reservation=setup_reservation,
            amount=Decimal('300.00')
        )
        Invoice.objects.create(
            reservation=setup_reservation,
            amount=Decimal('150.00')
        )
        
        # Verificar que as faturas existem
        assert Invoice.objects.count() == 2
        
        # Excluir a reserva
        setup_reservation.delete()
        
        # Verificar que as faturas foram excluídas em cascata
        assert Invoice.objects.count() == 0
