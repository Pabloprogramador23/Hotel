"""
URL configuration for hotel_hms project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static
from .views import home

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home, name='home'),
    path('api/', include('apps.api.urls')),
    path('reservations/', include('apps.reservations.urls')),
    path('rooms/', include('apps.rooms.urls')),
    # Usando apenas uma versão do caminho para evitar conflitos
    path('checkin_checkout/', include('apps.checkin_checkout.urls', namespace='checkin_checkout')),
    path('finance/', include(('apps.finance.urls', 'finance'), namespace='finance')),
    path('reports/', include('apps.reports.urls')),
    path('settings/', include('apps.settings_manager.urls')),
]

# Adiciona URLs para arquivos estáticos
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Adiciona URLs para arquivos de mídia apenas em ambiente de desenvolvimento
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
