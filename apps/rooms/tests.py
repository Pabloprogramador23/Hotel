import pytest
from django.urls import reverse
from django.contrib.auth.models import User, Permission
from django.contrib.contenttypes.models import ContentType
from datetime import date, timedelta

from apps.rooms.models import Room, MaintenanceRecord


@pytest.mark.django_db
class TestRoomModel:
    """Testes para o modelo Room"""
    
    def test_create_room(self):
        """Teste da criação básica de um quarto"""
        room = Room.objects.create(
            number="101",
            room_type="single",
            status="clean",
            description="A nice single room"
        )
        
        assert room.number == "101"
        assert room.room_type == "single"
        assert room.status == "clean"
        assert room.description == "A nice single room"
        assert str(room) == "Room 101 (single)"
    
    def test_room_number_unique(self):
        """Teste de unicidade do número do quarto"""
        Room.objects.create(
            number="102",
            room_type="double"
        )
        
        # Tenta criar outro quarto com o mesmo número
        with pytest.raises(Exception):
            Room.objects.create(
                number="102",
                room_type="single"
            )
    
    def test_room_type_choices(self):
        """Teste para garantir que os tipos de quarto são válidos"""
        # Tipos válidos
        room1 = Room.objects.create(number="103", room_type="single")
        room2 = Room.objects.create(number="104", room_type="double")
        room3 = Room.objects.create(number="105", room_type="suite")
        
        assert room1.room_type == "single"
        assert room2.room_type == "double"
        assert room3.room_type == "suite"


@pytest.mark.django_db
class TestMaintenanceRecordModel:
    """Testes para o modelo MaintenanceRecord"""
    
    @pytest.fixture
    def setup_room(self):
        """Fixture para criar um quarto para testes"""
        return Room.objects.create(
            number="201",
            room_type="double",
            status="clean"
        )
    
    def test_create_maintenance_record(self, setup_room):
        """Teste de criação de um registro de manutenção"""
        record = MaintenanceRecord.objects.create(
            room=setup_room,
            description="Fixed the air conditioning"
        )
        
        assert record.room == setup_room
        assert record.description == "Fixed the air conditioning"
        assert record.date == date.today()
        assert str(record) == f"Maintenance for Room {setup_room.number} on {date.today()}"
    
    def test_maintenance_record_relationship(self, setup_room):
        """Teste da relação entre quarto e registros de manutenção"""
        # Criar vários registros de manutenção para um quarto
        record1 = MaintenanceRecord.objects.create(
            room=setup_room,
            description="Fixed the TV"
        )
        record2 = MaintenanceRecord.objects.create(
            room=setup_room,
            description="Replaced the shower head"
        )
        
        # Verificar se o quarto tem os registros de manutenção relacionados
        maintenance_records = setup_room.maintenance_records.all()
        assert maintenance_records.count() == 2
        assert record1 in maintenance_records
        assert record2 in maintenance_records
    
    def test_cascade_delete(self, setup_room):
        """Teste da exclusão em cascata quando um quarto é excluído"""
        MaintenanceRecord.objects.create(
            room=setup_room,
            description="Regular maintenance"
        )
        
        # Verificar que o registro existe
        assert MaintenanceRecord.objects.count() == 1
        
        # Excluir o quarto
        setup_room.delete()
        
        # Verificar que o registro de manutenção também foi excluído
        assert MaintenanceRecord.objects.count() == 0


@pytest.mark.django_db
class TestRoomViews:
    """Testes para as views do aplicativo rooms"""
    
    @pytest.fixture
    def setup_user_with_permissions(self):
        """Fixture para criar usuário com permissões necessárias"""
        user = User.objects.create_user(username='testuser', password='password')
        content_type = ContentType.objects.get_for_model(Room)
        
        # Adicionar todas as permissões para o modelo
        permissions = Permission.objects.filter(content_type=content_type)
        for perm in permissions:
            user.user_permissions.add(perm)
        
        return user
    
    @pytest.fixture
    def setup_sample_rooms(self):
        """Fixture para criar quartos de exemplo para testes"""
        rooms = [
            Room.objects.create(number=f"30{i}", room_type="single" if i % 3 == 0 else "double" if i % 3 == 1 else "suite", 
                               status="clean" if i % 2 == 0 else "dirty")
            for i in range(5)
        ]
        return rooms
    
    def test_room_list_view(self, client, setup_user_with_permissions, setup_sample_rooms):
        """Teste da view de listagem de quartos"""
        client.login(username='testuser', password='password')
        response = client.get(reverse('room-list'))
        
        assert response.status_code == 200
        for room in setup_sample_rooms:
            assert room.number in str(response.content)
