from django.db import models
from django.core.exceptions import ValidationError
from apps.reservations.models import Reservation

class CheckIn(models.Model):
    reservation = models.OneToOneField(Reservation, on_delete=models.CASCADE)
    document_scanned = models.BooleanField(default=False)
    check_in_time = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, null=True)
    completed = models.BooleanField(default=False)

    def __str__(self):
        return f"CheckIn for {self.reservation}"
    
    def clean(self):
        # Verificar se já existe check-in para esta reserva
        try:
            existing_checkin = CheckIn.objects.get(reservation=self.reservation)
            if existing_checkin.id != self.id:  # Se não for o mesmo registro
                raise ValidationError("Já existe um check-in para a reserva")
        except CheckIn.DoesNotExist:
            pass
        
        # Verificar se a reserva está confirmada
        if self.reservation.status not in ['confirmed', 'pending']:
            raise ValidationError(f"Não é possível fazer check-in para uma reserva com status '{self.reservation.status}'")
    
    def save(self, *args, **kwargs):
        # Validar o objeto
        self.clean()
        # Atualizar campos da reserva
        self.reservation.checked_in = True
        self.reservation.check_in_time = self.check_in_time
        self.reservation.status = 'checked_in'
        # Atualizar status do quarto para 'occupied'
        room = self.reservation.room
        room.status = 'occupied'
        room.save()
        # Salvar a reserva
        self.reservation.save()
        # Salvar o check-in
        super().save(*args, **kwargs)

class CheckOut(models.Model):
    reservation = models.OneToOneField(Reservation, on_delete=models.CASCADE)
    check_in = models.OneToOneField(CheckIn, on_delete=models.CASCADE, null=True, blank=True)
    check_out_time = models.DateTimeField(auto_now_add=True)
    has_pending_payments = models.BooleanField(default=False)
    notes = models.TextField(blank=True, null=True)
    completed = models.BooleanField(default=False)

    def __str__(self):
        return f"CheckOut for {self.reservation}"
    
    def clean(self):
        # Verificar se a reserva tem check-in
        if not self.reservation.checked_in:
            raise ValidationError("Não é possível fazer check-out sem check-in prévio")
        # Verificar se a reserva já tem check-out
        if self.reservation.checked_out:
            raise ValidationError("Esta reserva já possui check-out")
        # Bloquear check-out se houver faturas em aberto
        from apps.finance.models import Invoice
        unpaid_invoices = Invoice.objects.filter(reservation=self.reservation, paid=False).count()
        if unpaid_invoices > 0:
            raise ValidationError(f"Existem {unpaid_invoices} faturas pendentes. Todas as faturas devem ser pagas antes do check-out.")
    
    def save(self, *args, **kwargs):
        # Buscar o check-in associado
        if not self.check_in:
            try:
                self.check_in = CheckIn.objects.get(reservation=self.reservation)
            except CheckIn.DoesNotExist:
                pass
        # Validar o objeto
        self.clean()
        # Atualizar campos da reserva
        self.reservation.checked_out = True
        self.reservation.check_out_time = self.check_out_time
        self.reservation.status = 'checked_out'
        # Atualizar status do quarto para 'needs_cleaning'
        room = self.reservation.room
        room.status = 'needs_cleaning'
        room.save()
        # Salvar a reserva
        self.reservation.save()
        # Salvar o check-out
        super().save(*args, **kwargs)
