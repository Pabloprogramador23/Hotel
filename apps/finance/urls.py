from django.urls import path
from . import views

urlpatterns = [
    path('invoices/', views.list_invoices, name='list_invoices'),
    path('all-invoices/', views.list_all_invoices_view, name='all_invoices'),
    path('reservations/<int:reservation_id>/invoices/', views.list_invoices, name='list_reservation_invoices'),
    path('reservations/<int:reservation_id>/create-invoice/', views.create_invoice, name='create_invoice'),
    path('invoices/<int:invoice_id>/mark-paid/', views.mark_invoice_paid, name='mark_invoice_paid'),
    path('reservation/<int:reservation_id>/invoices/', views.reservation_invoices_view, name='reservation_invoices'),
    
    # URLs para despesas
    path('expenses/', views.expense_list, name='expense_list'),
    path('expenses/create/', views.create_expense, name='create_expense'),
    path('expenses/<int:expense_id>/delete/', views.delete_expense, name='delete_expense'),
]