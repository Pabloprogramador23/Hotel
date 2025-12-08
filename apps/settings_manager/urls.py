from django.urls import path
from . import views

app_name = 'settings_manager'

urlpatterns = [
    path('', views.settings_list, name='list'),
    path('create/', views.settings_create, name='create'),
    path('edit/<int:pk>/', views.settings_edit, name='edit'),
    path('delete/<int:pk>/', views.settings_delete, name='delete'),
    path('modal/pricing/', views.settings_pricing_modal, name='pricing_modal'),
    path('pricing/update/<int:room_id>/', views.update_room_price, name='update_room_price'),
]