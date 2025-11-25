from django.contrib import admin
from django.utils.html import format_html
from jalali_date.admin import ModelAdminJalaliMixin
from jalali_date import datetime2jalali, date2jalali
from .models import Announcement, Feedback, InsuranceForm, PhoneBook


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


@admin.register(Feedback)
class FeedbackAdmin(ModelAdminJalaliMixin, admin.ModelAdmin):
    list_display = (
        'user', 'message_preview', 'status', 'read_by', 'jalali_created_at', 'jalali_read_at'
    )
    list_filter = ('status', 'created_at', 'read_at')
    search_fields = ('user__username', 'user__employee_number', 'message', 'user__first_name', 'user__last_name')
    ordering = ('-created_at',)
    raw_id_fields = ('user', 'read_by')
    readonly_fields = ('created_at', 'updated_at', 'read_at')
    
    fieldsets = (
        ('اطلاعات نظر', {
            'fields': ('user', 'message', 'status')
        }),
        ('اطلاعات خوانده شدن', {
            'fields': ('read_by', 'read_at')
        }),
        ('اطلاعات سیستم', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def message_preview(self, obj):
        """پیش‌نمایش متن نظر"""
        if len(obj.message) > 50:
            return obj.message[:50] + '...'
        return obj.message
    message_preview.short_description = 'متن نظر'
    
    def jalali_created_at(self, obj):
        if obj.created_at:
            return datetime2jalali(obj.created_at).strftime('%Y/%m/%d %H:%M')
        return '-'
    jalali_created_at.short_description = 'تاریخ ایجاد (شمسی)'
    jalali_created_at.admin_order_field = 'created_at'
    
    def jalali_read_at(self, obj):
        if obj.read_at:
            return datetime2jalali(obj.read_at).strftime('%Y/%m/%d %H:%M')
        return '-'
    jalali_read_at.short_description = 'تاریخ خوانده شدن (شمسی)'
    jalali_read_at.admin_order_field = 'read_at'


@admin.register(InsuranceForm)
class InsuranceFormAdmin(ModelAdminJalaliMixin, admin.ModelAdmin):
    list_display = (
        'user', 'file_preview', 'status', 'reviewed_by', 'jalali_created_at', 'jalali_reviewed_at'
    )
    list_filter = ('status', 'created_at', 'reviewed_at')
    search_fields = ('user__username', 'user__employee_number', 'description', 'user__first_name', 'user__last_name')
    ordering = ('-created_at',)
    raw_id_fields = ('user', 'reviewed_by')
    readonly_fields = ('created_at', 'updated_at', 'reviewed_at')
    
    fieldsets = (
        ('اطلاعات فرم', {
            'fields': ('user', 'file', 'description', 'status')
        }),
        ('اطلاعات بررسی', {
            'fields': ('reviewed_by', 'reviewed_at', 'review_comment')
        }),
        ('اطلاعات سیستم', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def file_preview(self, obj):
        """پیش‌نمایش فایل"""
        if obj.file:
            return format_html(
                '<a href="{}" target="_blank">مشاهده فایل</a>',
                obj.file.url
            )
        return "بدون فایل"
    file_preview.short_description = 'فایل'
    
    def jalali_created_at(self, obj):
        if obj.created_at:
            return datetime2jalali(obj.created_at).strftime('%Y/%m/%d %H:%M')
        return '-'
    jalali_created_at.short_description = 'تاریخ ایجاد (شمسی)'
    jalali_created_at.admin_order_field = 'created_at'
    
    def jalali_reviewed_at(self, obj):
        if obj.reviewed_at:
            return datetime2jalali(obj.reviewed_at).strftime('%Y/%m/%d %H:%M')
        return '-'
    jalali_reviewed_at.short_description = 'تاریخ بررسی (شمسی)'
    jalali_reviewed_at.admin_order_field = 'reviewed_at'


@admin.register(PhoneBook)
class PhoneBookAdmin(ModelAdminJalaliMixin, admin.ModelAdmin):
    list_display = (
        'title', 'phone', 'jalali_created_at'
    )
    list_filter = ('created_at',)
    search_fields = ('title', 'phone')
    ordering = ('title',)
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('اطلاعات دفترچه تلفن', {
            'fields': ('title', 'phone')
        }),
        ('اطلاعات سیستم', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def jalali_created_at(self, obj):
        if obj.created_at:
            return datetime2jalali(obj.created_at).strftime('%Y/%m/%d %H:%M')
        return '-'
    jalali_created_at.short_description = 'تاریخ ایجاد (شمسی)'
    jalali_created_at.admin_order_field = 'created_at'


