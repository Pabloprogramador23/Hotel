from django.db import models
from django.core.exceptions import ValidationError

# Create your models here.

class Reservation(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ('checked_in', 'Checked In'),   # Status adicionado
        ('checked_out', 'Checked Out'), # Status adicionado
    ]

    guest_name = models.CharField(max_length=255)
    guest_email = models.EmailField(blank=True, null=True)
    room = models.ForeignKey('rooms.Room', on_delete=models.CASCADE)
    check_in_date = models.DateField()
    check_out_date = models.DateField()
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default='pending')  # Aumentei max_length para acomodar 'checked_out'
    notes = models.TextField(blank=True, null=True)
    
    # Campos adicionados para rastrear check-in/check-out
    checked_in = models.BooleanField(default=False)
    checked_out = models.BooleanField(default=False)
    check_in_time = models.DateTimeField(null=True, blank=True)
    check_out_time = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Reservation {self.id} - {self.guest_name}"
    
    def clean(self):
        # Validar que a data de check-out não seja anterior à data de check-in
        if self.check_out_date and self.check_in_date and self.check_out_date < self.check_in_date:
            raise ValidationError("Check-out date cannot be earlier than check-in date")
            
    def save(self, *args, **kwargs):
        # Executar validações
        self.clean()
        
        # Verificar sobreposições apenas para reservas não canceladas
        if self.status not in ['cancelled', 'checked_out']:
            overlapping_reservations = Reservation.objects.filter(
                room=self.room,
                check_in_date__lt=self.check_out_date,
                check_out_date__gt=self.check_in_date,
                status__in=['pending', 'confirmed', 'checked_in']  # Considerar reservas ativas
            ).exclude(pk=self.pk)

            if overlapping_reservations.exists():
                raise ValueError("Overbooking detected for room {}".format(self.room.number))

        super().save(*args, **kwargs)
