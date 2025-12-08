from django.http import JsonResponse
from django.db.models import Count, Q
from datetime import date, datetime, timedelta
from apps.rooms.models import Room, MaintenanceRecord
from apps.reservations.models import Reservation
from apps.checkin_checkout.models import CheckIn, CheckOut
import json
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth.decorators import user_passes_test, login_required
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import serializers, status
from rest_framework.generics import RetrieveUpdateAPIView, ListCreateAPIView, ListAPIView
from django.shortcuts import get_object_or_404

class DashboardStatsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        today = date.today()
        total_rooms = Room.objects.count()
        occupied_rooms = Room.objects.filter(status='occupied').count()
        occupancy_rate = round((occupied_rooms / total_rooms * 100) if total_rooms > 0 else 0, 1)
        todays_checkins = Reservation.objects.filter(check_in_date=today).count()
        today_start = datetime.combine(today, datetime.min.time())
        today_end = datetime.combine(today, datetime.max.time())
        completed_checkins = CheckIn.objects.filter(check_in_time__range=(today_start, today_end)).count()
        pending_checkins = todays_checkins - completed_checkins
        todays_checkouts = Reservation.objects.filter(check_out_date=today).count()
        completed_checkouts = CheckOut.objects.filter(check_out_time__range=(today_start, today_end)).count()
        pending_checkouts = todays_checkouts - completed_checkouts
        return Response({
            'occupancy_rate': occupancy_rate,
            'occupied_rooms': occupied_rooms,
            'available_rooms': total_rooms - occupied_rooms,
            'todays_checkins': todays_checkins,
            'completed_checkins': completed_checkins,
            'pending_checkins': pending_checkins,
            'todays_checkouts': todays_checkouts,
            'completed_checkouts': completed_checkouts,
            'pending_checkouts': pending_checkouts
        })

class AvailableRoomsSerializer(serializers.Serializer):
    room_type = serializers.CharField(required=False)
    check_in = serializers.DateField(required=False)
    check_out = serializers.DateField(required=False)

class AvailableRoomsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = AvailableRoomsSerializer(data=request.GET)
        serializer.is_valid(raise_exception=True)
        room_type = serializer.validated_data.get('room_type')
        check_in = serializer.validated_data.get('check_in', date.today())
        check_out = serializer.validated_data.get('check_out', date.today() + timedelta(days=1))
        rooms = Room.objects.all()
        if room_type and room_type != 'all':
            rooms = rooms.filter(room_type=room_type)
        unavailable_rooms = Reservation.objects.filter(
            check_in_date__lt=check_out,
            check_out_date__gt=check_in,
            status__in=['pending', 'confirmed', 'checked_in']
        ).values_list('room_id', flat=True)
        available_rooms = rooms.exclude(id__in=unavailable_rooms)
        rooms_data = [
            {
                'id': room.id,
                'number': room.number,
                'room_type': room.room_type,
                'status': room.status,
                'description': room.description
            }
            for room in available_rooms
        ]
        return Response(rooms_data)

@require_http_methods(["POST"])
@csrf_protect
@login_required
def reservation_create(request):
    """API para criar uma nova reserva"""
    try:
        data = json.loads(request.body)

        # Validar dados obrigatórios
        required_fields = ['guest_name', 'guest_email', 'room_id', 'check_in_date', 'check_out_date']
        for field in required_fields:
            if field not in data:
                return JsonResponse({'message': f'Campo obrigatório ausente: {field}'}, status=400)

        # Validar datas
        try:
            check_in_date = datetime.strptime(data['check_in_date'], '%Y-%m-%d').date()
            check_out_date = datetime.strptime(data['check_out_date'], '%Y-%m-%d').date()
            if check_out_date <= check_in_date:
                return JsonResponse({'message': 'A data de check-out deve ser posterior à data de check-in'}, status=400)
        except ValueError:
            return JsonResponse({'message': 'Formato de data inválido. Use YYYY-MM-DD.'}, status=400)

        # Obter o quarto
        try:
            room = Room.objects.get(id=data['room_id'])
        except Room.DoesNotExist:
            return JsonResponse({'message': 'Quarto não encontrado'}, status=404)

        # Criar a reserva
        reservation = Reservation(
            guest_name=data['guest_name'],
            guest_email=data['guest_email'],
            room=room,
            check_in_date=check_in_date,
            check_out_date=check_out_date,
            notes=data.get('notes', ''),
            status=data.get('status', 'confirmed')
        )

        # Tentar salvar (a validação acontece no método save)
        try:
            reservation.save()
            return JsonResponse({'id': reservation.id, 'message': 'Reserva criada com sucesso'})
        except ValueError as e:
            return JsonResponse({'message': str(e)}, status=400)

    except json.JSONDecodeError:
        return JsonResponse({'message': 'Dados JSON inválidos'}, status=400)
    except Exception as e:
        return JsonResponse({'message': f'Erro ao criar reserva: {str(e)}'}, status=500)

class ReservationFilterSerializer(serializers.Serializer):
    date = serializers.DateField(required=False)
    status = serializers.ChoiceField(choices=[
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ('checked_in', 'Checked In'),
        ('checked_out', 'Checked Out'),
    ], required=False)
    guest = serializers.CharField(required=False, allow_blank=True)

# Exemplo de uso seguro em uma view DRF:
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from apps.reservations.models import Reservation
from apps.rooms.models import Room
from django.db.models import Q
from datetime import datetime

class ReservationListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = ReservationFilterSerializer(data=request.GET)
        serializer.is_valid(raise_exception=True)
        filters = serializer.validated_data
        reservations = Reservation.objects.all().select_related('room')
        if 'date' in filters:
            reservations = reservations.filter(
                Q(check_in_date=filters['date']) | Q(check_out_date=filters['date'])
            )
        if 'status' in filters:
            reservations = reservations.filter(status=filters['status'])
        if 'guest' in filters:
            reservations = reservations.filter(guest_name__icontains=filters['guest'])
        # Paginação pode ser aplicada aqui se necessário
        data = [
            {
                'id': r.id,
                'guest_name': r.guest_name,
                'room': r.room.number,
                'check_in_date': r.check_in_date,
                'check_out_date': r.check_out_date,
                'status': r.status,
            }
            for r in reservations
        ]
        return Response(data)

# Serializers para quartos
class RoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Room
        fields = ['id', 'number', 'room_type', 'status', 'description', 'created_at', 'updated_at']

class MaintenanceRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = MaintenanceRecord
        fields = ['id', 'room', 'date', 'description', 'resolution', 'maintenance_type']

# Views para gerenciamento de quartos
class RoomListView(ListCreateAPIView):
    """API para listar e criar quartos"""
    queryset = Room.objects.all()
    serializer_class = RoomSerializer
    
    def get_permissions(self):
        return [IsAuthenticated()]

class RoomDetailView(RetrieveUpdateAPIView):
    """API para obter detalhes de um quarto e atualizá-lo"""
    queryset = Room.objects.all()
    serializer_class = RoomSerializer
    
    def get_permissions(self):
        return [IsAuthenticated()]

class RoomStatusUpdateView(APIView):
    """API para atualizar o status de um quarto"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request, pk):
        try:
            room = get_object_or_404(Room, pk=pk)
            
            # Obter o novo status do quarto
            data = json.loads(request.body)
            new_status = data.get('status')
            
            # Validar o status
            valid_statuses = ['available', 'occupied', 'clean', 'dirty', 'maintenance', 'needs_cleaning']
            if not new_status or new_status not in valid_statuses:
                return Response({
                    'success': False,
                    'message': 'Status inválido. Deve ser um dos seguintes: ' + ', '.join(valid_statuses)
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Atualizar o status
            room.status = new_status
            room.save()
            
            return Response({
                'success': True,
                'message': f'Status do quarto {room.number} atualizado para {new_status}',
                'room': RoomSerializer(room).data
            })
            
        except json.JSONDecodeError:
            return Response({
                'success': False,
                'message': 'Dados JSON inválidos'
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'success': False,
                'message': f'Erro ao atualizar status: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class RoomMaintenanceHistoryView(ListAPIView):
    """API para listar o histórico de manutenção de um quarto"""
    serializer_class = MaintenanceRecordSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        room_id = self.kwargs.get('pk')
        return MaintenanceRecord.objects.filter(room_id=room_id).order_by('-date')

class ReservationCalendarView(APIView):
    """API para fornecer dados do calendário de reservas do mês"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        # Obter o ano e mês da consulta
        try:
            year = int(request.GET.get('year', datetime.now().year))
            month = int(request.GET.get('month', datetime.now().month))
        except ValueError:
            return Response({'error': 'Ano e mês devem ser números inteiros'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Criar datas de início e fim do mês
        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = date(year, month + 1, 1) - timedelta(days=1)
            
        # Buscar todas as reservas deste mês
        reservations = Reservation.objects.filter(
            Q(check_in_date__lte=end_date, check_out_date__gte=start_date),
            status__in=['confirmed', 'checked_in']
        ).values('check_in_date', 'check_out_date')
        
        # Extrair dias com check-in, check-out e dias ocupados
        checkins = []
        checkouts = []
        occupied_days = []
        
        for reservation in reservations:
            check_in = reservation['check_in_date']
            check_out = reservation['check_out_date']
            
            # Adicionar data de check-in se estiver no mês atual
            if start_date <= check_in <= end_date:
                checkins.append(check_in.isoformat())
            
            # Adicionar data de check-out se estiver no mês atual
            if start_date <= check_out <= end_date:
                checkouts.append(check_out.isoformat())
            
            # Calcular todos os dias de ocupação (incluindo check-in, excluindo check-out)
            current_date = check_in
            while current_date < check_out:
                if start_date <= current_date <= end_date:
                    occupied_days.append(current_date.isoformat())
                current_date += timedelta(days=1)
        
        # Remover duplicatas
        checkins = list(set(checkins))
        checkouts = list(set(checkouts))
        occupied_days = list(set(occupied_days))
        
        return Response({
            'checkins': checkins,
            'checkouts': checkouts,
            'occupied_days': occupied_days
        })
