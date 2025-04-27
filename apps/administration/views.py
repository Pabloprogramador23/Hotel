from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import SystemSetting

@login_required
def admin_dashboard(request):
    return render(request, 'administration/dashboard.html')

@login_required
def system_settings(request):
    settings = SystemSetting.objects.all()
    return render(request, 'administration/settings.html', {'settings': settings})

@login_required
def user_management(request):
    return render(request, 'administration/users.html')
