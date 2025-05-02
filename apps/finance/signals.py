from django.db.models.signals import post_save
from django.dispatch import receiver
from datetime import timedelta
from apps.reservations.models import Reservation
from apps.settings_manager.models import SystemSetting
from .models import Invoice

@receiver(post_save, sender=Reservation)
def create_invoice_for_reservation(sender, instance, created, **kwargs):
    # Só cria fatura se a reserva for confirmada e não houver fatura existente
    if instance.status == 'confirmed' and not Invoice.objects.filter(reservation=instance).exists():
        # Calcular o valor da fatura com base nas configurações do sistema
        amount = calculate_reservation_amount(instance)
        Invoice.objects.create(reservation=instance, amount=amount)

def calculate_reservation_amount(reservation):
    """
    Calcula o valor total da reserva com base nas configurações do sistema
    e nas características da reserva.
    """
    # Obter a configuração de preço diário para o tipo de quarto
    room_type = reservation.room.room_type
    rate_key = f"daily_rate_{room_type}"
    
    try:
        daily_rate = float(SystemSetting.objects.get(key=rate_key).value)
    except SystemSetting.DoesNotExist:
        # Preço padrão caso a configuração não exista
        daily_rate = 160.00
    
    # Calcular número de diárias
    stay_length = (reservation.check_out_date - reservation.check_in_date).days
    if stay_length <= 0:
        stay_length = 1  # Mínimo de uma diária
    
    # Calcular o valor base da estadia
    amount = daily_rate * stay_length
    
    # Adicionar taxa de limpeza se configurada
    try:
        cleaning_fee = float(SystemSetting.objects.get(key="cleaning_fee").value)
        amount += cleaning_fee
    except SystemSetting.DoesNotExist:
        # Não adiciona taxa se não configurada
        pass
    
    return amount
