from django.contrib import admin
from .models import Center


@admin.register(Center)
class CenterAdmin(admin.ModelAdmin):
    list_display = ('name','english_name', 'city', 'phone', 'email', 'is_active', 'created_at')
    list_filter = ('is_active', 'city', 'created_at')
    search_fields = ('name', 'english_name', 'city', 'phone', 'email')
    ordering = ('name',)
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'english_name', 'city', 'address')
        }),
        ('Contact Information', {
            'fields': ('phone', 'email')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
    )


