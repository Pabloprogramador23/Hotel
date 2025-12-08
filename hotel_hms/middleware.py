import os
from django.http import HttpResponse


class MaintenanceModeMiddleware:
    """Retorna 503 quando MAINTENANCE_MODE=True, exceto para rotas liberadas."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        maintenance_on = os.environ.get('MAINTENANCE_MODE', 'False').lower() == 'true'
        allow_prefixes = (
            '/admin/',
            '/health',
            '/static/',
            '/media/',
        )
        if maintenance_on and not request.path.startswith(allow_prefixes):
            return HttpResponse('Serviço em manutenção', status=503)
        return self.get_response(request)
