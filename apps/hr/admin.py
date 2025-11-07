from django.contrib import admin
from django.utils.html import format_html
from jalali_date.admin import ModelAdminJalaliMixin
from jalali_date import datetime2jalali, date2jalali
from .models import Announcement


@admin.register(Announcement)
class AnnouncementAdmin(ModelAdminJalaliMixin, admin.ModelAdmin):
    list_display = (
        'title', 'get_centers_display', 'created_by', 'jalali_publish_date', 
        'is_active', 'jalali_created_at', 'image_preview'
    )
    list_filter = ('is_active', 'centers', 'created_by', 'publish_date', 'created_at')
    search_fields = ('title', 'lead', 'content', 'centers__name', 'created_by__username')
    ordering = ('-publish_date',)
    raw_id_fields = ('created_by',)
    filter_horizontal = ('centers',)
    
    def jalali_publish_date(self, obj):
        if obj.publish_date:
            return datetime2jalali(obj.publish_date).strftime('%Y/%m/%d %H:%M')
        return '-'
    jalali_publish_date.short_description = 'تاریخ انتشار (شمسی)'
    jalali_publish_date.admin_order_field = 'publish_date'
    
    def jalali_created_at(self, obj):
        if obj.created_at:
            return datetime2jalali(obj.created_at).strftime('%Y/%m/%d %H:%M')
        return '-'
    jalali_created_at.short_description = 'تاریخ ایجاد (شمسی)'
    jalali_created_at.admin_order_field = 'created_at'
    
    fieldsets = (
        ('اطلاعات اصلی', {
            'fields': ('title', 'lead', 'content', 'image', 'centers')
        }),
        ('تنظیمات انتشار', {
            'fields': ('publish_date', 'is_active')
        }),
        ('اطلاعات سیستم', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_centers_display(self, obj):
        """نمایش مراکز در لیست"""
        centers = obj.centers.all()
        if centers.exists():
            return ', '.join([center.name for center in centers[:3]])
        return 'بدون مرکز'
    get_centers_display.short_description = 'مراکز'
    
    readonly_fields = ('created_at', 'updated_at')
    
    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" width="50" height="50" style="border-radius: 5px;" />',
                obj.image.url
            )
        return "بدون تصویر"
    image_preview.short_description = 'تصویر'
    
    def save_model(self, request, obj, form, change):
        if not change:  # اگر در حال ایجاد است
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


