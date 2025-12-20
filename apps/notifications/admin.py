"""
Admin configuration for notifications app
"""
from django.contrib import admin
from .models import PushSubscription


@admin.register(PushSubscription)
class PushSubscriptionAdmin(admin.ModelAdmin):
    """Admin interface for PushSubscription"""
    list_display = ['user', 'endpoint_short', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'user__email', 'endpoint']
    readonly_fields = ['created_at', 'updated_at']
    raw_id_fields = ['user']

    def endpoint_short(self, obj):
        """نمایش کوتاه endpoint"""
        return obj.endpoint[:50] + '...' if len(obj.endpoint) > 50 else obj.endpoint
    endpoint_short.short_description = 'Endpoint'


