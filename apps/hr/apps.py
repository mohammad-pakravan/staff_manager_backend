"""
Configuration برای hr app
"""
from django.apps import AppConfig


class HrConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.hr'
    verbose_name = 'نیروی انسانی'

    def ready(self):
        """Import signals هنگام آماده شدن app"""
        import apps.hr.signals  # noqa

