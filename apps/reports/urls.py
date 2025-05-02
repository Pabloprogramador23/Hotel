from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('', views.report_list, name='list'),
    path('occupancy/', views.occupancy_report, name='occupancy'),
    path('revenue/', views.revenue_report, name='revenue'),
    path('checkins/', views.checkins_report, name='checkins'),
    path('cash-flow/', views.cash_flow_report, name='cash_flow'),
    path('financial/', views.financial_report, name='financial_report'),
    path('financial-consolidated/', views.financial_consolidated_report, name='financial_consolidated'),
]