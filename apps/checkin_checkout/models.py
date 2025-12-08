from django.core.exceptions import ValidationError
from django.db import models

from apps.reservations.models import Reservation


class CheckIn(models.Model):
    reservation = models.OneToOneField(Reservation, on_delete=models.CASCADE, related_name='checkin')
    document_scanned = models.BooleanField(default=False)
    started_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, null=True)
    completed = models.BooleanField(default=True)

    class Meta:
        ordering = ['-started_at']

    def __str__(self):
        return f"Check-in #{self.pk} - Quarto {self.reservation.room.numero}"

    def clean(self):
        if self.reservation.ocupando:
            raise ValidationError('A reserva já está em andamento.')

    def save(self, *args, **kwargs):
        creating = self._state.adding
        self.clean()
        super().save(*args, **kwargs)
        if creating:
            self.reservation.room.ocupar()


class CheckOut(models.Model):
    reservation = models.OneToOneField(Reservation, on_delete=models.CASCADE, related_name='checkout')
    check_in = models.OneToOneField(CheckIn, on_delete=models.CASCADE, null=True, blank=True)
    finished_at = models.DateTimeField(auto_now_add=True)
    has_pending_payments = models.BooleanField(default=False)
    notes = models.TextField(blank=True, null=True)
    completed = models.BooleanField(default=True)

    class Meta:
        ordering = ['-finished_at']

    def __str__(self):
        return f"Check-out #{self.pk} - Quarto {self.reservation.room.numero}"

    def clean(self):
        if not self.reservation.ocupando:
            raise ValidationError('Esta reserva já foi encerrada.')

        has_pending = self.reservation.hospedes.filter(pago=False).exists()
        if has_pending and not self.has_pending_payments:
            raise ValidationError('Existem hóspedes com valores pendentes.')

    def save(self, *args, **kwargs):
        if not self.check_in:
            self.check_in = CheckIn.objects.filter(reservation=self.reservation).first()
        self.clean()
        super().save(*args, **kwargs)
        self.reservation.encerrar(self.finished_at)
