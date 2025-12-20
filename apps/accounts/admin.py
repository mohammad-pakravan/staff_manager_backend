from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
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
    list_display = ('get_profile_image_thumbnail', 'username', 'employee_number', 'first_name', 'last_name', 'role', 'position', 'manager', 'get_centers_display', 'max_reservations_per_day', 'max_guest_reservations_per_day', 'is_active', 'date_joined')
    list_filter = ('role', 'is_active', 'is_staff', 'is_superuser', 'centers', 'position', 'date_joined')
    search_fields = ('username', 'employee_number', 'first_name', 'last_name', 'email')
    ordering = ('-date_joined',)
    filter_horizontal = ('centers',)
    raw_id_fields = ('manager',)  # اضافه کردن جستجو برای فیلد manager
    readonly_fields = ('get_profile_image_preview',)
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('اطلاعات اضافی', {
            'fields': ('employee_number', 'role', 'position', 'manager', 'centers', 'phone_number', 'profile_image', 'get_profile_image_preview', 'max_reservations_per_day', 'max_guest_reservations_per_day')
        }),
    )
    
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('اطلاعات اضافی', {
            'fields': ('employee_number', 'role', 'position', 'manager', 'centers', 'phone_number', 'profile_image', 'max_reservations_per_day', 'max_guest_reservations_per_day')
        }),
    )
    
    def get_profile_image_thumbnail(self, obj):
        """نمایش تصویر کوچک در لیست"""
        if obj.profile_image:
            return format_html(
                '<img src="{}" width="40" height="40" style="border-radius: 50%; object-fit: cover;" />',
                obj.profile_image.url
            )
        return format_html('<div style="width: 40px; height: 40px; border-radius: 50%; background-color: #ddd; display: inline-block;"></div>')
    get_profile_image_thumbnail.short_description = 'تصویر'
    
    def get_profile_image_preview(self, obj):
        """نمایش پیش‌نمایش تصویر در صفحه ویرایش"""
        if obj.profile_image:
            return format_html(
                '<img src="{}" width="200" height="200" style="border-radius: 50%; object-fit: cover; border: 2px solid #ddd;" />',
                obj.profile_image.url
            )
        return 'تصویری انتخاب نشده است'
    get_profile_image_preview.short_description = 'پیش‌نمایش تصویر'
    
    def get_centers_display(self, obj):
        """نمایش مراکز کاربر در لیست"""
        centers = obj.centers.all()
        if centers.exists():
            return ', '.join([center.name for center in centers[:3]])
        return 'بدون مرکز'
    get_centers_display.short_description = 'مراکز'
