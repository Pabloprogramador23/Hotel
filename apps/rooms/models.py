from django.db import models

# Create your models here.

class Room(models.Model):
    ROOM_TYPES = [
        ('single', 'Single'),
        ('double', 'Double'),
        ('suite', 'Suite'),
    ]

    number = models.CharField(max_length=10, unique=True)
    room_type = models.CharField(max_length=10, choices=ROOM_TYPES)
    status = models.CharField(max_length=20, default='clean')
    description = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Room {self.number} ({self.room_type})"


class MaintenanceRecord(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='maintenance_records')
    description = models.TextField()
    date = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"Maintenance for Room {self.room.number} on {self.date}"
