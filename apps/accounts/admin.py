from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'employee_number', 'first_name', 'last_name', 'role', 'center', 'max_reservations_per_day', 'max_guest_reservations_per_day', 'is_active', 'date_joined')
    list_filter = ('role', 'is_active', 'is_staff', 'is_superuser', 'center', 'date_joined')
    search_fields = ('username', 'employee_number', 'first_name', 'last_name', 'email')
    ordering = ('-date_joined',)
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Additional Info', {'fields': ('employee_number', 'role', 'center', 'phone_number', 'max_reservations_per_day', 'max_guest_reservations_per_day')}),
    )
    
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Additional Info', {'fields': ('employee_number', 'role', 'center', 'phone_number', 'max_reservations_per_day', 'max_guest_reservations_per_day')}),
    )
