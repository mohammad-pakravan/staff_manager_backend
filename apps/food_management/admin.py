from django.contrib import admin
from django.utils.html import format_html
from jalali_date.admin import ModelAdminJalaliMixin
from jalali_date import datetime2jalali, date2jalali
from .models import (
    Meal, MealType, WeeklyMenu, DailyMenu, 
    FoodReservation, FoodReport, GuestReservation
)


@admin.register(Meal)
class MealAdmin(ModelAdminJalaliMixin, admin.ModelAdmin):
    list_display = ('title', 'restaurant', 'jalali_date', 'meal_type', 'jalali_created_at', 'is_active', 'image_preview')
    list_filter = ('date', 'meal_type', 'restaurant', 'is_active', 'created_at')
    search_fields = ('title', 'description', 'restaurant')
    ordering = ('title',)
    
    def jalali_date(self, obj):
        if obj.date:
            return date2jalali(obj.date).strftime('%Y/%m/%d')
        return '-'
    jalali_date.short_description = 'تاریخ شمسی'
    jalali_date.admin_order_field = 'date'
    
    def jalali_created_at(self, obj):
        if obj.created_at:
            return datetime2jalali(obj.created_at).strftime('%Y/%m/%d %H:%M')
        return '-'
    jalali_created_at.short_description = 'تاریخ ایجاد (شمسی)'
    jalali_created_at.admin_order_field = 'created_at'
    
    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" width="50" height="50" style="border-radius: 5px;" />',
                obj.image.url
            )
        return "بدون تصویر"
    image_preview.short_description = 'تصویر'


@admin.register(MealType)
class MealTypeAdmin(ModelAdminJalaliMixin, admin.ModelAdmin):
    list_display = ('name', 'start_time', 'end_time', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name',)
    ordering = ('start_time',)


@admin.register(WeeklyMenu)
class WeeklyMenuAdmin(ModelAdminJalaliMixin, admin.ModelAdmin):
    list_display = ('center', 'jalali_week_start', 'jalali_week_end', 'is_active', 'created_by', 'jalali_created_at')
    list_filter = ('is_active', 'center', 'created_at')
    search_fields = ('center__name',)
    ordering = ('-week_start_date',)
    raw_id_fields = ('center', 'created_by')
    
    def jalali_week_start(self, obj):
        if obj.week_start_date:
            return date2jalali(obj.week_start_date).strftime('%Y/%m/%d')
        return '-'
    jalali_week_start.short_description = 'شروع هفته (شمسی)'
    jalali_week_start.admin_order_field = 'week_start_date'
    
    def jalali_week_end(self, obj):
        if obj.week_end_date:
            return date2jalali(obj.week_end_date).strftime('%Y/%m/%d')
        return '-'
    jalali_week_end.short_description = 'پایان هفته (شمسی)'
    jalali_week_end.admin_order_field = 'week_end_date'
    
    def jalali_created_at(self, obj):
        if obj.created_at:
            return datetime2jalali(obj.created_at).strftime('%Y/%m/%d %H:%M')
        return '-'
    jalali_created_at.short_description = 'تاریخ ایجاد (شمسی)'
    jalali_created_at.admin_order_field = 'created_at'


@admin.register(DailyMenu)
class DailyMenuAdmin(ModelAdminJalaliMixin, admin.ModelAdmin):
    list_display = (
        'weekly_menu', 'jalali_date', 'meal_type', 'meals_count', 
        'max_reservations_per_meal', 'is_available'
    )
    list_filter = ('date', 'meal_type', 'is_available', 'weekly_menu__center')
    search_fields = ('weekly_menu__center__name',)
    ordering = ('-date', 'meal_type__start_time')
    raw_id_fields = ('weekly_menu', 'meal_type')
    filter_horizontal = ('meals',)
    
    def jalali_date(self, obj):
        if obj.date:
            return date2jalali(obj.date).strftime('%Y/%m/%d')
        return '-'
    jalali_date.short_description = 'تاریخ شمسی'
    jalali_date.admin_order_field = 'date'
    
    def meals_count(self, obj):
        return obj.meals.count()
    meals_count.short_description = 'تعداد غذاها'


@admin.register(FoodReservation)
class FoodReservationAdmin(ModelAdminJalaliMixin, admin.ModelAdmin):
    list_display = (
        'user', 'jalali_date', 'get_meal_title', 'quantity', 'status', 'amount', 
        'jalali_reservation_date', 'jalali_cancellation_deadline', 'can_cancel_status'
    )
    list_filter = ('status', 'reservation_date', 'daily_menu__meal_type', 'daily_menu__weekly_menu__center')
    search_fields = ('user__username', 'user__employee_number', 'meal__title')
    ordering = ('-reservation_date',)
    raw_id_fields = ('user', 'daily_menu', 'meal')
    
    def jalali_date(self, obj):
        if obj.daily_menu and obj.daily_menu.date:
            return date2jalali(obj.daily_menu.date).strftime('%Y/%m/%d')
        return '-'
    jalali_date.short_description = 'تاریخ شمسی'
    jalali_date.admin_order_field = 'daily_menu__date'
    
    def get_meal_title(self, obj):
        return obj.meal.title if obj.meal else "بدون غذا"
    get_meal_title.short_description = 'غذا'
    get_meal_title.admin_order_field = 'meal__title'
    
    def jalali_reservation_date(self, obj):
        if obj.reservation_date:
            return datetime2jalali(obj.reservation_date).strftime('%Y/%m/%d %H:%M')
        return '-'
    jalali_reservation_date.short_description = 'تاریخ رزرو (شمسی)'
    jalali_reservation_date.admin_order_field = 'reservation_date'
    
    def jalali_cancellation_deadline(self, obj):
        if obj.cancellation_deadline:
            return datetime2jalali(obj.cancellation_deadline).strftime('%Y/%m/%d %H:%M')
        return '-'
    jalali_cancellation_deadline.short_description = 'مهلت لغو (شمسی)'
    jalali_cancellation_deadline.admin_order_field = 'cancellation_deadline'
    
    def can_cancel_status(self, obj):
        if obj.can_cancel():
            return format_html('<span style="color: green;">✓ قابل لغو</span>')
        else:
            return format_html('<span style="color: red;">✗ غیرقابل لغو</span>')
    can_cancel_status.short_description = 'وضعیت لغو'


@admin.register(GuestReservation)
class GuestReservationAdmin(ModelAdminJalaliMixin, admin.ModelAdmin):
    list_display = (
        'guest_first_name', 'guest_last_name', 'host_user', 'jalali_date', 'get_meal_title', 
        'status', 'amount', 'jalali_reservation_date', 'jalali_cancellation_deadline', 'can_cancel_status'
    )
    list_filter = ('status', 'reservation_date', 'daily_menu__meal_type', 'daily_menu__weekly_menu__center')
    search_fields = ('guest_first_name', 'guest_last_name', 'host_user__username', 'host_user__employee_number', 'meal__title')
    ordering = ('-reservation_date',)
    raw_id_fields = ('host_user', 'daily_menu', 'meal')
    
    def jalali_date(self, obj):
        if obj.daily_menu and obj.daily_menu.date:
            return date2jalali(obj.daily_menu.date).strftime('%Y/%m/%d')
        return '-'
    jalali_date.short_description = 'تاریخ شمسی'
    jalali_date.admin_order_field = 'daily_menu__date'
    
    def get_meal_title(self, obj):
        return obj.meal.title if obj.meal else "بدون غذا"
    get_meal_title.short_description = 'غذا'
    get_meal_title.admin_order_field = 'meal__title'
    
    def jalali_reservation_date(self, obj):
        if obj.reservation_date:
            return datetime2jalali(obj.reservation_date).strftime('%Y/%m/%d %H:%M')
        return '-'
    jalali_reservation_date.short_description = 'تاریخ رزرو (شمسی)'
    jalali_reservation_date.admin_order_field = 'reservation_date'
    
    def jalali_cancellation_deadline(self, obj):
        if obj.cancellation_deadline:
            return datetime2jalali(obj.cancellation_deadline).strftime('%Y/%m/%d %H:%M')
        return '-'
    jalali_cancellation_deadline.short_description = 'مهلت لغو (شمسی)'
    jalali_cancellation_deadline.admin_order_field = 'cancellation_deadline'
    
    def can_cancel_status(self, obj):
        if obj.can_cancel():
            return format_html('<span style="color: green;">✓ قابل لغو</span>')
        else:
            return format_html('<span style="color: red;">✗ غیرقابل لغو</span>')
    can_cancel_status.short_description = 'وضعیت لغو'


@admin.register(FoodReport)
class FoodReportAdmin(ModelAdminJalaliMixin, admin.ModelAdmin):
    list_display = ('center', 'jalali_report_date', 'total_reservations', 'total_served', 'total_cancelled', 'jalali_created_at')
    list_filter = ('report_date', 'center', 'created_at')
    search_fields = ('center__name',)
    ordering = ('-report_date',)
    raw_id_fields = ('center',)
    
    def jalali_report_date(self, obj):
        if obj.report_date:
            return date2jalali(obj.report_date).strftime('%Y/%m/%d')
        return '-'
    jalali_report_date.short_description = 'تاریخ گزارش (شمسی)'
    jalali_report_date.admin_order_field = 'report_date'
    
    def jalali_created_at(self, obj):
        if obj.created_at:
            return datetime2jalali(obj.created_at).strftime('%Y/%m/%d %H:%M')
        return '-'
    jalali_created_at.short_description = 'تاریخ ایجاد (شمسی)'
    jalali_created_at.admin_order_field = 'created_at'


