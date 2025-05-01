import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from django.contrib.auth.models import User
from datetime import date, timedelta
from apps.rooms.models import Room
from apps.reservations.models import Reservation
from rest_framework_simplejwt.tokens import RefreshToken


@pytest.mark.django_db
def test_api_reservation_list_jwt():
    user = User.objects.create_user(username='apitest', password='1234')
    room = Room.objects.create(number="301", room_type="single", status="clean")
    today = date.today()
    Reservation.objects.create(guest_name="API1", room=room, check_in_date=today, check_out_date=today+timedelta(days=2), status="confirmed")
    Reservation.objects.create(guest_name="API2", room=room, check_in_date=today, check_out_date=today+timedelta(days=2), status="pending")
    refresh = RefreshToken.for_user(user)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    url = reverse('api:reservation_list')
    response = client.get(url, {'status': 'pending'})
    assert response.status_code == 200
    data = response.json()
    assert any(r['guest_name'] == 'API2' for r in data)
    assert all(r['status'] == 'pending' for r in data)
