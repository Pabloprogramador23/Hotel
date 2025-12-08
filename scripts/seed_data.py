import os
import django
import random
from datetime import date, timedelta
from decimal import Decimal

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "hotel_hms.settings")
django.setup()

from django.contrib.auth import get_user_model
from apps.rooms.models import Room
from apps.reservations.models import Reservation, ReservationGuest

User = get_user_model()

def run():
    print("🧹 Cleaning up...")
    Room.objects.all().delete()
    Reservation.objects.all().delete()
    User.objects.exclude(is_superuser=True).delete() # Keep admin if exists

    print("🏨 Creating Rooms...")
    rooms = []
    for i in range(101, 111):
        room = Room.objects.create(
            number=str(i),
            room_type=random.choice(['STANDARD', 'LUXE', 'SUITE']),
            price_per_night=Decimal('150.00'),
            capacity=random.randint(2, 4),
            status='AVAILABLE'
        )
        rooms.append(room)

    print("📅 Creating Reservations...")
    # Active Reservation 1
    r1 = Reservation.objects.create(
        room=rooms[0],
        guest_name="João Silva",
        check_in_date=date.today(),
        check_out_date=date.today() + timedelta(days=2),
        status='checked_in',
        total_price=Decimal('300.00')
    )
    # Add a guest to r1
    ReservationGuest.objects.create(
        reservation=r1,
        name="Maria Silva",
        amount_due=Decimal('80.00'),
        is_paid=True,
        payment_method='PIX'
    )

    # Active Reservation 2
    r2 = Reservation.objects.create(
        room=rooms[2],
        guest_name="Ana Costa",
        check_in_date=date.today(),
        check_out_date=date.today() + timedelta(days=1),
        status='confirmed',
        total_price=Decimal('150.00')
    )

    # Active Reservation 3 (Pending)
    r3 = Reservation.objects.create(
        room=rooms[5],
        guest_name="Carlos Souza",
        check_in_date=date.today(),
        check_out_date=date.today() + timedelta(days=3),
        status='checked_in',
        total_price=Decimal('450.00')
    )

    print("✅ Database Seeded Successfully!")

if __name__ == "__main__":
    run()
