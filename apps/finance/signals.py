from django.db.models.signals import post_save
from django.dispatch import receiver
from apps.reservations.models import Reservation
from .models import Invoice

@receiver(post_save, sender=Reservation)
def create_invoice_for_reservation(sender, instance, created, **kwargs):
    # Só cria fatura se a reserva for confirmada e não houver fatura existente
    if instance.status == 'confirmed' and not Invoice.objects.filter(reservation=instance).exists():
        # Valor fictício, ajuste conforme sua lógica de precificação
        amount = 160.00
        Invoice.objects.create(reservation=instance, amount=amount)
