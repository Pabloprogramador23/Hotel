from django.urls import path

from . import views

urlpatterns = [
    path('cash-overview/', views.cash_overview, name='cash_overview'),
    path('reservation-balances/', views.reservation_balances, name='reservation_balances'),
    path('adjustments/', views.list_adjustments, name='list_adjustments'),
    path('adjustments/create/', views.create_adjustment, name='create_adjustment'),
    path('adjustments/<int:adjustment_id>/delete/', views.delete_adjustment, name='delete_adjustment'),

    path('expenses/', views.expense_list, name='expense_list'),
    path('expenses/create/', views.create_expense, name='create_expense'),
    path('expenses/<int:expense_id>/delete/', views.delete_expense, name='delete_expense'),

    path('extra-income/', views.extra_income_list, name='extra_income_list'),
    path('extra-income/create/', views.create_extra_income, name='create_extra_income'),
]