import os
import django
from django.conf import settings

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "hotel_hms.settings")
django.setup()

from apps.reservations.models import Reservation

print(f"Total Reservations: {Reservation.objects.count()}")
for r in Reservation.objects.all():
    print(f"ID: {r.id} | Guest: {r.guest_name} | Room: {r.room.number} | Status: {r.status} | CheckIn: {r.check_in_date}")
