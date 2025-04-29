import pytest
from django.urls import reverse
from django.contrib.auth.models import User, Permission
from django.contrib.contenttypes.models import ContentType
from datetime import date, timedelta

from apps.reservations.models import Reservation
from apps.rooms.models import Room


@pytest.mark.django_db
class TestReservationModel:
    """Testes para o modelo Reservation"""
    
    @pytest.fixture
    def setup_room(self):
        """Fixture para criar um quarto para testes"""
        return Room.objects.create(
            number="301",
            room_type="double",
            status="clean"
        )
    
    def test_create_reservation(self, setup_room):
        """Teste da criação básica de uma reserva"""
        check_in = date.today() + timedelta(days=1)
        check_out = check_in + timedelta(days=3)
        
        reservation = Reservation.objects.create(
            guest_name="John Doe",
            room=setup_room,
            check_in_date=check_in,
            check_out_date=check_out,
            status="confirmed"
        )
        
        assert reservation.guest_name == "John Doe"
        assert reservation.room == setup_room
        assert reservation.check_in_date == check_in
        assert reservation.check_out_date == check_out
        assert reservation.status == "confirmed"
        assert str(reservation) == f"Reservation {reservation.id} - John Doe"
    
    def test_invalid_dates(self, setup_room):
        """Teste de validação para check-out anterior ao check-in"""
        check_in = date.today() + timedelta(days=5)
        check_out = date.today() + timedelta(days=2)  # Check-out antes do check-in
        
        # Deve lançar uma exceção
        with pytest.raises(ValueError, match="Check-out date cannot be earlier than check-in date"):
            Reservation.objects.create(
                guest_name="Jane Smith",
                room=setup_room,
                check_in_date=check_in,
                check_out_date=check_out
            )
    
    def test_overlapping_reservations(self, setup_room):
        """Teste para detecção de sobreposição de reservas (overbooking)"""
        # Criar primeira reserva
        check_in1 = date.today() + timedelta(days=10)
        check_out1 = check_in1 + timedelta(days=5)
        reservation1 = Reservation.objects.create(
            guest_name="Guest One",
            room=setup_room,
            check_in_date=check_in1,
            check_out_date=check_out1,
            status="confirmed"
        )
        
        # Tentar criar uma reserva com datas sobrepostas
        check_in2 = check_in1 + timedelta(days=2)  # Durante a estadia do primeiro hóspede
        check_out2 = check_out1 + timedelta(days=3)
        
        # Deve lançar uma exceção devido à sobreposição
        with pytest.raises(ValueError, match="Overbooking detected"):
            Reservation.objects.create(
                guest_name="Guest Two",
                room=setup_room,
                check_in_date=check_in2,
                check_out_date=check_out2,
                status="confirmed"
            )
    
    def test_cancelled_reservation_no_overlap(self, setup_room):
        """Teste para verificar que reservas canceladas não geram conflito de overbooking"""
        # Criar primeira reserva (cancelada)
        check_in1 = date.today() + timedelta(days=20)
        check_out1 = check_in1 + timedelta(days=5)
        reservation1 = Reservation.objects.create(
            guest_name="Cancelled Guest",
            room=setup_room,
            check_in_date=check_in1,
            check_out_date=check_out1,
            status="cancelled"  # Reserva cancelada
        )
        
        # Criar nova reserva com as mesmas datas (deve funcionar porque a anterior está cancelada)
        reservation2 = Reservation.objects.create(
            guest_name="New Guest",
            room=setup_room,
            check_in_date=check_in1,
            check_out_date=check_out1,
            status="confirmed"
        )
        
        # Verificar que ambas as reservas existem sem erro
        assert Reservation.objects.count() == 2
        assert reservation2.status == "confirmed"


@pytest.mark.django_db
class TestReservationViews:
    """Testes para as views do aplicativo reservations"""
    
    @pytest.fixture
    def setup_user_with_permissions(self):
        """Fixture para criar usuário com permissões necessárias"""
        user = User.objects.create_user(username='testuser', password='password')
        content_type = ContentType.objects.get_for_model(Reservation)
        
        # Adicionar todas as permissões para o modelo
        permissions = Permission.objects.filter(content_type=content_type)
        for perm in permissions:
            user.user_permissions.add(perm)
        
        return user
    
    @pytest.fixture
    def setup_room(self):
        """Fixture para criar um quarto para testes"""
        return Room.objects.create(
            number="401",
            room_type="suite",
            status="clean"
        )
    
    @pytest.fixture
    def setup_sample_reservations(self, setup_room):
        """Fixture para criar reservas de exemplo para testes"""
        base_date = date.today()
        reservations = []
        
        for i in range(5):
            check_in = base_date + timedelta(days=i*10)
            check_out = check_in + timedelta(days=3)
            
            reservation = Reservation.objects.create(
                guest_name=f"Guest {i}",
                room=setup_room,
                check_in_date=check_in,
                check_out_date=check_out,
                status="confirmed" if i % 3 != 0 else "pending"
            )
            reservations.append(reservation)
        
        return reservations
    
    def test_reservation_list_view(self, client, setup_user_with_permissions, setup_sample_reservations):
        """Teste da view de listagem de reservas"""
        client.login(username='testuser', password='password')
        response = client.get(reverse('reservation-list'))
        
        assert response.status_code == 200
        for reservation in setup_sample_reservations:
            assert reservation.guest_name in str(response.content)
