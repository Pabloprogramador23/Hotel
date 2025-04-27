import pytest
from django.urls import reverse

@pytest.mark.django_db
def test_report_list_view(client):
    url = reverse('reports:list')
    response = client.get(url)
    assert response.status_code == 200

@pytest.mark.django_db
def test_occupancy_report_view(client):
    url = reverse('reports:occupancy')
    response = client.get(url)
    assert response.status_code == 200

@pytest.mark.django_db
def test_revenue_report_view(client):
    url = reverse('reports:revenue')
    response = client.get(url)
    assert response.status_code == 200

@pytest.mark.django_db
def test_checkins_report_view(client):
    url = reverse('reports:checkins')
    response = client.get(url)
    assert response.status_code == 200
