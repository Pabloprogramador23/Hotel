from django.urls import path
from . import views

app_name = 'settings_manager'

urlpatterns = [
    path('', views.settings_list, name='list'),
    path('create/', views.settings_create, name='create'),
    path('edit/<int:pk>/', views.settings_edit, name='edit'),
    path('delete/<int:pk>/', views.settings_delete, name='delete'),
]