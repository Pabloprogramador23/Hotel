from django.db import models

# Create your models here.

class Reservation(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
    ]

    guest_name = models.CharField(max_length=255)
    room = models.ForeignKey('rooms.Room', on_delete=models.CASCADE)
    check_in_date = models.DateField()
    check_out_date = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Reservation {self.id} - {self.guest_name}"

    def save(self, *args, **kwargs):
        overlapping_reservations = Reservation.objects.filter(
            room=self.room,
            check_in_date__lt=self.check_out_date,
            check_out_date__gt=self.check_in_date,
        ).exclude(pk=self.pk)

        if overlapping_reservations.exists():
            raise ValueError("Overbooking detected for room {}".format(self.room.number))

        super().save(*args, **kwargs)
