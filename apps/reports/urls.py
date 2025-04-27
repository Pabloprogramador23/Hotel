from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('', views.report_list, name='list'),
    path('occupancy/', views.occupancy_report, name='occupancy'),
    path('revenue/', views.revenue_report, name='revenue'),
    path('checkins/', views.checkins_report, name='checkins'),
]