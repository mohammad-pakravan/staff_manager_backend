from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'employee_number', 'first_name', 'last_name', 'role', 'get_centers_display', 'max_reservations_per_day', 'max_guest_reservations_per_day', 'is_active', 'date_joined')
    list_filter = ('role', 'is_active', 'is_staff', 'is_superuser', 'centers', 'date_joined')
    search_fields = ('username', 'employee_number', 'first_name', 'last_name', 'email')
    ordering = ('-date_joined',)
    filter_horizontal = ('centers',)
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Additional Info', {'fields': ('employee_number', 'role', 'centers', 'phone_number', 'max_reservations_per_day', 'max_guest_reservations_per_day')}),
    )
    
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Additional Info', {'fields': ('employee_number', 'role', 'centers', 'phone_number', 'max_reservations_per_day', 'max_guest_reservations_per_day')}),
    )
    
    def get_centers_display(self, obj):
        """نمایش مراکز کاربر در لیست"""
        centers = obj.centers.all()
        if centers.exists():
            return ', '.join([center.name for center in centers[:3]])
        return 'بدون مرکز'
    get_centers_display.short_description = 'مراکز'
