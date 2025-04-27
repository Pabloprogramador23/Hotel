from django.db import models
from apps.reservations.models import Reservation

class CheckIn(models.Model):
    reservation = models.OneToOneField(Reservation, on_delete=models.CASCADE)
    document_scanned = models.BooleanField(default=False)
    check_in_time = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"CheckIn for Reservation {self.reservation.id}"

class CheckOut(models.Model):
    reservation = models.OneToOneField(Reservation, on_delete=models.CASCADE)
    payment_status = models.BooleanField(default=False)
    check_out_time = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"CheckOut for Reservation {self.reservation.id}"
