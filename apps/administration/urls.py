from django.urls import path
from . import views

urlpatterns = [
    path('', views.admin_dashboard, name='admin-dashboard'),
    path('settings/', views.system_settings, name='system-settings'),
    path('users/', views.user_management, name='user-management'),
]