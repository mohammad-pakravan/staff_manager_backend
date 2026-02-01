from django.contrib import admin
from .models import Center


@admin.register(Center)
class CenterAdmin(admin.ModelAdmin):
    list_display = ('name', 'logo', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name',)
    ordering = ('name',)
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name','english_name', 'logo')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
    )


