from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Position


@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'created_at', 'updated_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'description')
    ordering = ('name',)
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('اطلاعات اصلی', {
            'fields': ('name', 'description', 'is_active')
        }),
        ('اطلاعات زمانی', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'employee_number', 'first_name', 'last_name', 'role', 'position', 'manager', 'get_centers_display', 'max_reservations_per_day', 'max_guest_reservations_per_day', 'is_active', 'date_joined')
    list_filter = ('role', 'is_active', 'is_staff', 'is_superuser', 'centers', 'position', 'date_joined')
    search_fields = ('username', 'employee_number', 'first_name', 'last_name', 'email')
    ordering = ('-date_joined',)
    filter_horizontal = ('centers',)
    raw_id_fields = ('manager',)  # اضافه کردن جستجو برای فیلد manager
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Additional Info', {'fields': ('employee_number', 'role', 'position', 'manager', 'centers', 'phone_number', 'max_reservations_per_day', 'max_guest_reservations_per_day')}),
    )
    
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Additional Info', {'fields': ('employee_number', 'role', 'position', 'manager', 'centers', 'phone_number', 'max_reservations_per_day', 'max_guest_reservations_per_day')}),
    )
    
    def get_centers_display(self, obj):
        """نمایش مراکز کاربر در لیست"""
        centers = obj.centers.all()
        if centers.exists():
            return ', '.join([center.name for center in centers[:3]])
        return 'بدون مرکز'
    get_centers_display.short_description = 'مراکز'
