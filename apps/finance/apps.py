from django.apps import AppConfig


class FinanceConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.finance'
    app_label = 'finance'

    def ready(self):
        import apps.finance.signals  # noqa
