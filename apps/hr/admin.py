from django.contrib import admin
from django.utils.html import format_html
from jalali_date.admin import ModelAdminJalaliMixin
from jalali_date import datetime2jalali, date2jalali
from .models import Announcement, AnnouncementReadStatus, Feedback, InsuranceForm, PhoneBook, Story


@admin.register(Announcement)
class AnnouncementAdmin(ModelAdminJalaliMixin, admin.ModelAdmin):
    list_display = (
        'title', 'get_centers_display', 'is_announcement', 'is_news', 'send_to_all_users', 'created_by', 
        'jalali_publish_date', 'is_active', 'jalali_created_at', 'image_preview'
    )
    list_filter = ('is_active', 'is_announcement', 'is_news', 'send_to_all_users', 'centers', 'created_by', 'publish_date', 'created_at')
    search_fields = ('title', 'lead', 'content', 'centers__name', 'created_by__username')
    ordering = ('-publish_date',)
    raw_id_fields = ('created_by',)
    filter_horizontal = ('centers', 'target_users')
    
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
            'fields': ('title', 'lead', 'content', 'image')
        }),
        ('نوع انتشار', {
            'fields': ('is_announcement', 'is_news'),
            'description': 'حداقل یکی از گزینه‌ها باید انتخاب شود'
        }),
        ('ارسال به', {
            'fields': ('centers', 'send_to_all_users', 'target_users'),
            'description': 'برای خبر: فقط مراکز. برای اطلاعیه: مراکز و/یا ارسال به کل کاربران و/یا کاربران خاص'
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
    
    def get_type_display(self, obj):
        """نمایش نوع (اطلاعیه/خبر)"""
        types = []
        if obj.is_announcement:
            types.append('اطلاعیه')
        if obj.is_news:
            types.append('خبر')
        return ', '.join(types) if types else 'تعریف نشده'
    get_type_display.short_description = 'نوع'
    
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
        # اعتبارسنجی: حداقل یکی از is_announcement یا is_news باید True باشد
        if not obj.is_announcement and not obj.is_news:
            from django.core.exceptions import ValidationError
            raise ValidationError('حداقل یکی از "به عنوان اطلاعیه منتشر شود" یا "به عنوان خبر منتشر شود" باید انتخاب شود.')
        super().save_model(request, obj, form, change)


@admin.register(AnnouncementReadStatus)
class AnnouncementReadStatusAdmin(ModelAdminJalaliMixin, admin.ModelAdmin):
    list_display = (
        'announcement', 'user', 'is_read', 'read_at', 'jalali_read_at', 'jalali_created_at'
    )
    list_filter = ('read_at', 'created_at')
    search_fields = ('announcement__title', 'user__username', 'user__first_name', 'user__last_name')
    ordering = ('-created_at',)
    raw_id_fields = ('announcement', 'user')
    readonly_fields = ('created_at', 'read_at')
    
    fieldsets = (
        ('اطلاعات', {
            'fields': ('announcement', 'user', 'read_at')
        }),
        ('اطلاعات سیستم', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def is_read(self, obj):
        """نمایش وضعیت خوانده شده"""
        if obj.read_at:
            return format_html('<span style="color: green;">✓ خوانده شده</span>')
        return format_html('<span style="color: red;">✗ خوانده نشده</span>')
    is_read.short_description = 'وضعیت'
    is_read.boolean = True
    
    def jalali_read_at(self, obj):
        if obj.read_at:
            return datetime2jalali(obj.read_at).strftime('%Y/%m/%d %H:%M')
        return '-'
    jalali_read_at.short_description = 'تاریخ خوانده شدن (شمسی)'
    jalali_read_at.admin_order_field = 'read_at'
    
    def jalali_created_at(self, obj):
        if obj.created_at:
            return datetime2jalali(obj.created_at).strftime('%Y/%m/%d %H:%M')
        return '-'
    jalali_created_at.short_description = 'تاریخ ایجاد (شمسی)'
    jalali_created_at.admin_order_field = 'created_at'


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


@admin.register(Story)
class StoryAdmin(ModelAdminJalaliMixin, admin.ModelAdmin):
    list_display = (
        'get_text_preview', 'created_by', 'content_type_display',
        'is_active', 'expiry_status', 'jalali_created_at', 'thumbnail_preview', 'content_preview'
    )
    list_filter = ('is_active', 'created_by', 'created_at', 'expiry_date')
    search_fields = ('text',   'created_by__username')
    ordering = ('-created_at',)
    raw_id_fields = ('created_by',)
   
    readonly_fields = ('created_at', 'updated_at', 'expiry_status_display')
    
    fieldsets = (
        ('اطلاعات اصلی', {
            'fields': ('text', 'thumbnail_image', 'content_file')
        }),
        ('تنظیمات', {
            'fields': ('is_active', 'expiry_date', 'expiry_status_display')
        }),
        ('اطلاعات سیستم', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_text_preview(self, obj):
        """پیش‌نمایش متن"""
        if obj.text:
            if len(obj.text) > 50:
                return obj.text[:50] + '...'
            return obj.text
        return 'بدون متن'
    get_text_preview.short_description = 'متن'
    
    def content_type_display(self, obj):
        """نمایش نوع محتوا"""
        content_type = obj.content_type
        if content_type == 'image':
            return 'عکس'
        elif content_type == 'video':
            return 'ویدیو'
        return 'بدون محتوا'
    content_type_display.short_description = 'نوع محتوا'
    
    def thumbnail_preview(self, obj):
        """پیش‌نمایش تصویر شاخص"""
        if obj.thumbnail_image:
            return format_html(
                '<img src="{}" width="50" height="50" style="border-radius: 5px;" />',
                obj.thumbnail_image.url
            )
        return "بدون تصویر شاخص"
    thumbnail_preview.short_description = 'تصویر شاخص'
    
    def content_preview(self, obj):
        """پیش‌نمایش محتوا"""
        if obj.content_file:
            content_type = obj.content_type
            if content_type == 'image':
                return format_html(
                    '<img src="{}" width="50" height="50" style="border-radius: 5px;" />',
                    obj.content_file.url
                )
            elif content_type == 'video':
                return format_html(
                    '<a href="{}" target="_blank">مشاهده ویدیو</a>',
                    obj.content_file.url
                )
        return "بدون محتوا"
    content_preview.short_description = 'محتوای قابل نمایش'
    
    def jalali_created_at(self, obj):
        if obj.created_at:
            return datetime2jalali(obj.created_at).strftime('%Y/%m/%d %H:%M')
        return '-'
    jalali_created_at.short_description = 'تاریخ ایجاد (شمسی)'
    jalali_created_at.admin_order_field = 'created_at'
    
    def expiry_status(self, obj):
        """نمایش وضعیت انقضا"""
        if not obj.expiry_date:
            return format_html('<span style="color: #999;">بدون انقضا</span>')
        
        if obj.is_expired:
            return format_html('<span style="color: red; font-weight: bold;">⏰ منقضی شده</span>')
        else:
            jalali_expiry = datetime2jalali(obj.expiry_date).strftime('%Y/%m/%d %H:%M')
            return format_html('<span style="color: green;">✅ تا {}</span>', jalali_expiry)
    expiry_status.short_description = 'وضعیت انقضا'
    expiry_status.admin_order_field = 'expiry_date'
    
    def expiry_status_display(self, obj):
        """نمایش وضعیت انقضا در صفحه ویرایش"""
        if not obj.expiry_date:
            return 'بدون تاریخ انقضا'
        
        if obj.is_expired:
            jalali_expiry = datetime2jalali(obj.expiry_date).strftime('%Y/%m/%d %H:%M')
            return f'⏰ منقضی شده (از {jalali_expiry})'
        else:
            jalali_expiry = datetime2jalali(obj.expiry_date).strftime('%Y/%m/%d %H:%M')
            return f'✅ فعال تا {jalali_expiry}'
    expiry_status_display.short_description = 'وضعیت انقضا'
    
    def save_model(self, request, obj, form, change):
        if not change:  # اگر در حال ایجاد است
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


