"""
Configuration برای food_management app
"""
from django.apps import AppConfig


class FoodManagementConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.food_management'
    verbose_name = 'مدیریت غذا'

    def ready(self):
        """Import signals هنگام آماده شدن app"""
        import apps.food_management.signals  # noqa


