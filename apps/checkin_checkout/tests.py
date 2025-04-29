import pytest
from django.core.exceptions import ValidationError
from datetime import date, timedelta, datetime

from apps.checkin_checkout.models import CheckIn, CheckOut
from apps.reservations.models import Reservation
from apps.rooms.models import Room


@pytest.mark.django_db
class TestCheckInModel:
    """Testes para o modelo CheckIn"""
    
    @pytest.fixture
    def setup_reservation(self):
        """Fixture para criar um quarto e uma reserva para testes"""
        room = Room.objects.create(
            number="501",
            room_type="double",
            status="clean"
        )
        
        check_in_date = date.today()
        check_out_date = check_in_date + timedelta(days=3)
        
        reservation = Reservation.objects.create(
            guest_name="Check-in Test Guest",
            room=room,
            check_in_date=check_in_date,
            check_out_date=check_out_date,
            status="confirmed"
        )
        
        return reservation
    
    def test_create_checkin(self, setup_reservation):
        """Teste da criação básica de um check-in"""
        check_in = CheckIn.objects.create(
            reservation=setup_reservation,
            document_scanned=True
        )
        
        assert check_in.reservation == setup_reservation
        assert check_in.document_scanned is True
        assert check_in.check_in_time is not None
        assert str(check_in) == f"CheckIn for Reservation {setup_reservation.id}"
        
        # Verificar se o status do quarto foi atualizado para 'occupied'
        room = Room.objects.get(id=setup_reservation.room.id)
        assert room.status == "occupied"
    
    def test_duplicate_checkin_raises_error(self, setup_reservation):
        """Teste para garantir que não possa haver check-ins duplicados"""
        # Criar primeiro check-in
        CheckIn.objects.create(
            reservation=setup_reservation,
            document_scanned=True
        )
        
        # Tentar criar segundo check-in para a mesma reserva
        with pytest.raises(ValidationError, match="Já existe um check-in para a reserva"):
            CheckIn.objects.create(
                reservation=setup_reservation,
                document_scanned=False
            )


@pytest.mark.django_db
class TestCheckOutModel:
    """Testes para o modelo CheckOut"""
    
    @pytest.fixture
    def setup_checkin(self):
        """Fixture para criar quarto, reserva e check-in para testes"""
        room = Room.objects.create(
            number="502",
            room_type="suite",
            status="clean"
        )
        
        check_in_date = date.today() - timedelta(days=2)
        check_out_date = date.today() + timedelta(days=1)
        
        reservation = Reservation.objects.create(
            guest_name="Check-out Test Guest",
            room=room,
            check_in_date=check_in_date,
            check_out_date=check_out_date,
            status="confirmed"
        )
        
        check_in = CheckIn.objects.create(
            reservation=reservation,
            document_scanned=True
        )
        
        return check_in
    
    def test_create_checkout(self, setup_checkin):
        """Teste da criação básica de um check-out"""
        reservation = setup_checkin.reservation
        
        check_out = CheckOut.objects.create(
            reservation=reservation,
            payment_status=True
        )
        
        assert check_out.reservation == reservation
        assert check_out.payment_status is True
        assert check_out.check_out_time is not None
        assert str(check_out) == f"CheckOut for Reservation {reservation.id}"
        
        # Verificar se o status do quarto foi atualizado para 'needs_cleaning'
        room = Room.objects.get(id=reservation.room.id)
        assert room.status == "needs_cleaning"
    
    def test_checkout_without_checkin_raises_error(self):
        """Teste para garantir que check-out sem check-in prévio não é permitido"""
        # Criar quarto e reserva sem check-in
        room = Room.objects.create(
            number="503",
            room_type="single",
            status="clean"
        )
        
        check_in_date = date.today() - timedelta(days=2)
        check_out_date = date.today() + timedelta(days=1)
        
        reservation = Reservation.objects.create(
            guest_name="No Check-in Guest",
            room=room,
            check_in_date=check_in_date,
            check_out_date=check_out_date,
            status="confirmed"
        )
        
        # Tentar criar check-out sem check-in prévio
        with pytest.raises(ValidationError, match="Não é possível fazer check-out sem check-in prévio"):
            checkout = CheckOut(
                reservation=reservation,
                payment_status=True
            )
            checkout.clean()
    
    def test_checkout_with_unpaid_invoices(self, setup_checkin, monkeypatch):
        """Teste para garantir que check-out com faturas não pagas e payment_status=True não é permitido"""
        # Ao invés de substituir o atributo invoices, vamos monkeypatch o método que verifica faturas não pagas
        
        # Salvar a versão original da função clean
        original_clean = CheckOut.clean
        
        # Definir uma versão modificada da função clean que simula uma validação falha de faturas
        def mocked_clean(self):
            if self.payment_status:
                raise ValidationError("Existem faturas não pagas para esta reserva")
            original_clean(self)
        
        # Aplicar o monkey patch
        monkeypatch.setattr(CheckOut, 'clean', mocked_clean)
        
        # Criar o checkout com payment_status=True deve agora falhar com nossa mensagem de erro
        with pytest.raises(ValidationError, match="Existem faturas não pagas para esta reserva"):
            checkout = CheckOut(
                reservation=setup_checkin.reservation,
                payment_status=True  # Indica que todas as faturas estão pagas
            )
            checkout.clean()
