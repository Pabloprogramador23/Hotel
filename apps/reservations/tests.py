import pytest
from django.urls import reverse
from datetime import date, timedelta
from apps.rooms.models import Room
from apps.reservations.models import Reservation

@pytest.mark.django_db
def test_reservation_list_filter_by_date(client):
    room = Room.objects.create(number="201", room_type="single", status="clean")
    today = date.today()
    res1 = Reservation.objects.create(guest_name="A", room=room, check_in_date=today, check_out_date=today+timedelta(days=2), status="confirmed")
    res2 = Reservation.objects.create(guest_name="B", room=room, check_in_date=today+timedelta(days=1), check_out_date=today+timedelta(days=3), status="pending")
    url = reverse('reservations:reservation_list')
    response = client.get(url, {'date': today.strftime('%Y-%m-%d')})
    assert response.status_code == 200
    content = response.content.decode()
    assert "A" in content
    assert "B" not in content

@pytest.mark.django_db
def test_reservation_list_filter_by_status(client):
    room = Room.objects.create(number="202", room_type="single", status="clean")
    today = date.today()
    Reservation.objects.create(guest_name="C", room=room, check_in_date=today, check_out_date=today+timedelta(days=2), status="confirmed")
    Reservation.objects.create(guest_name="D", room=room, check_in_date=today, check_out_date=today+timedelta(days=2), status="pending")
    url = reverse('reservations:reservation_list')
    response = client.get(url, {'status': 'pending'})
    assert response.status_code == 200
    content = response.content.decode()
    assert "D" in content
    assert "C" not in content

@pytest.mark.django_db
def test_reservation_list_filter_by_guest(client):
    room = Room.objects.create(number="203", room_type="single", status="clean")
    today = date.today()
    Reservation.objects.create(guest_name="Eve", room=room, check_in_date=today, check_out_date=today+timedelta(days=2), status="confirmed")
    Reservation.objects.create(guest_name="Frank", room=room, check_in_date=today, check_out_date=today+timedelta(days=2), status="confirmed")
    url = reverse('reservations:reservation_list')
    response = client.get(url, {'guest': 'Eve'})
    assert response.status_code == 200
    content = response.content.decode()
    assert "Eve" in content
    assert "Frank" not in content
