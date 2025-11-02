from django.contrib import admin
from django.utils.html import format_html
from jalali_date.admin import ModelAdminJalaliMixin
from jalali_date import datetime2jalali, date2jalali
from .models import (
    Restaurant, BaseMeal, MealOption, MealType, DailyMenu, 
    FoodReservation, FoodReport, GuestReservation
)
# برای سازگاری با کدهای قبلی
Meal = BaseMeal


@admin.register(Restaurant)
class RestaurantAdmin(ModelAdminJalaliMixin, admin.ModelAdmin):
    list_display = ('name', 'center', 'phone', 'is_active', 'jalali_created_at')
    list_filter = ('center', 'is_active', 'created_at')
    search_fields = ('name', 'address', 'phone', 'email')
    ordering = ('name',)
    raw_id_fields = ('center',)
    
    def jalali_created_at(self, obj):
        if obj.created_at:
            return datetime2jalali(obj.created_at).strftime('%Y/%m/%d %H:%M')
        return '-'
    jalali_created_at.short_description = 'تاریخ ایجاد (شمسی)'
    jalali_created_at.admin_order_field = 'created_at'


class MealOptionInline(admin.TabularInline):
    """Inline برای نمایش و ویرایش MealOption ها در BaseMeal"""
    model = MealOption
    extra = 1
    fields = ('title', 'description', 'price', 'quantity', 'reserved_quantity', 'is_default', 'sort_order', 'is_active')
    readonly_fields = ('reserved_quantity',)  # تعداد رزرو شده فقط خواندنی است (خودکار به‌روزرسانی می‌شود)


@admin.register(BaseMeal)
class BaseMealAdmin(ModelAdminJalaliMixin, admin.ModelAdmin):
    list_display = ('title', 'meal_type', 'center', 'restaurant', 'jalali_cancellation_deadline', 'options_count', 'jalali_created_at', 'is_active', 'image_preview')
    list_filter = ('meal_type', 'center', 'restaurant', 'is_active', 'created_at', 'cancellation_deadline')
    search_fields = ('title', 'description')
    ordering = ('title',)
    raw_id_fields = ('meal_type', 'center', 'restaurant')
    fieldsets = (
        ('اطلاعات پایه', {
            'fields': ('title', 'description', 'image', 'meal_type', 'center', 'restaurant', 'is_active')
        }),
        ('مهلت لغو', {
            'fields': ('cancellation_deadline',),
            'description': 'اگر مهلت لغو مشخص نشود، همیشه می‌توان رزرو را لغو کرد.'
        }),
    )
    inlines = [MealOptionInline]
    
    def jalali_cancellation_deadline(self, obj):
        """مهلت لغو به شمسی"""
        if obj.cancellation_deadline:
            return datetime2jalali(obj.cancellation_deadline).strftime('%Y/%m/%d %H:%M')
        return 'بدون محدودیت'
    jalali_cancellation_deadline.short_description = 'مهلت لغو (شمسی)'
    jalali_cancellation_deadline.admin_order_field = 'cancellation_deadline'
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """فیلتر کردن رستوران‌ها بر اساس مرکز"""
        if db_field.name == 'restaurant':
            # اگر در حال ویرایش یک BaseMeal هستیم
            if hasattr(request, 'resolver_match') and request.resolver_match:
                try:
                    base_meal_id = request.resolver_match.kwargs.get('object_id')
                    if base_meal_id:
                        try:
                            base_meal = BaseMeal.objects.get(pk=base_meal_id)
                            if base_meal.center:
                                kwargs['queryset'] = Restaurant.objects.filter(
                                    center=base_meal.center,
                                    is_active=True
                                )
                        except BaseMeal.DoesNotExist:
                            pass
                except Exception:
                    pass
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
    
    def get_form(self, request, obj=None, **kwargs):
        """استفاده از ModelForm سفارشی برای validation"""
        from django import forms
        from .models import BaseMeal
        
        class BaseMealAdminForm(forms.ModelForm):
            class Meta:
                model = BaseMeal
                fields = '__all__'
            
            def clean(self):
                cleaned_data = super().clean()
                from django.core.exceptions import ValidationError
                
                restaurant = cleaned_data.get('restaurant')
                center = cleaned_data.get('center')
                
                if restaurant and center:
                    if restaurant.center != center:
                        raise ValidationError({
                            'restaurant': f'رستوران باید متعلق به مرکز "{center.name}" باشد. رستوران انتخاب شده متعلق به مرکز "{restaurant.center.name}" است.'
                        })
                
                return cleaned_data
        
        kwargs['form'] = BaseMealAdminForm
        return super().get_form(request, obj, **kwargs)
    
    def options_count(self, obj):
        return obj.options.count()
    options_count.short_description = 'تعداد گزینه‌ها'
    
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
    
    def get_form(self, request, obj=None, **kwargs):
        """تنظیم queryset رستوران‌ها در inline بر اساس مرکز"""
        form = super().get_form(request, obj, **kwargs)
        return form


# MealOption از ادمین حذف شد - فقط از طریق BaseMealAdmin قابل مدیریت است
try:
    admin.site.unregister(MealOption)
except admin.sites.NotRegistered:
    pass


# برای سازگاری با کدهای قبلی
MealAdmin = BaseMealAdmin


@admin.register(MealType)
class MealTypeAdmin(ModelAdminJalaliMixin, admin.ModelAdmin):
    list_display = ('name', 'start_time', 'end_time', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name',)
    ordering = ('start_time',)


@admin.register(DailyMenu)
class DailyMenuAdmin(ModelAdminJalaliMixin, admin.ModelAdmin):
    list_display = (
        'center', 'jalali_date', 'meal_type', 'meal_options_count', 
        'max_reservations_per_meal', 'is_available'
    )
    list_filter = ('date', 'meal_type', 'is_available', 'center')
    search_fields = ('center__name',)
    ordering = ('-date', 'meal_type__start_time')
    raw_id_fields = ('center', 'meal_type')
    filter_horizontal = ('meal_options',)
    
    def jalali_date(self, obj):
        if obj.date:
            return date2jalali(obj.date).strftime('%Y/%m/%d')
        return '-'
    jalali_date.short_description = 'تاریخ شمسی'
    jalali_date.admin_order_field = 'date'
    
    def meal_options_count(self, obj):
        return obj.meal_options.count()
    meal_options_count.short_description = 'تعداد غذاها'


@admin.register(FoodReservation)
class FoodReservationAdmin(ModelAdminJalaliMixin, admin.ModelAdmin):
    list_display = (
        'user', 'jalali_date', 'get_meal_option_title', 'quantity', 'status', 'amount', 
        'jalali_reservation_date', 'jalali_cancellation_deadline', 'can_cancel_status'
    )
    list_filter = ('status', 'reservation_date', 'daily_menu__meal_type', 'daily_menu__center')
    search_fields = ('user__username', 'user__employee_number', 'meal_option__title', 'meal_option__base_meal__title')
    ordering = ('-reservation_date',)
    raw_id_fields = ('user', 'daily_menu', 'meal_option')
    
    def jalali_date(self, obj):
        if obj.daily_menu and obj.daily_menu.date:
            return date2jalali(obj.daily_menu.date).strftime('%Y/%m/%d')
        return '-'
    jalali_date.short_description = 'تاریخ شمسی'
    jalali_date.admin_order_field = 'daily_menu__date'
    
    def get_meal_option_title(self, obj):
        if obj.meal_option:
            return f"{obj.meal_option.base_meal.title} - {obj.meal_option.title}"
        return "بدون غذا"
    get_meal_option_title.short_description = 'گزینه غذا'
    get_meal_option_title.admin_order_field = 'meal_option__title'
    
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
        'guest_first_name', 'guest_last_name', 'host_user', 'jalali_date', 'get_meal_option_title', 
        'status', 'amount', 'jalali_reservation_date', 'jalali_cancellation_deadline', 'can_cancel_status'
    )
    list_filter = ('status', 'reservation_date', 'daily_menu__meal_type', 'daily_menu__center')
    search_fields = ('guest_first_name', 'guest_last_name', 'host_user__username', 'host_user__employee_number', 'meal_option__title', 'meal_option__base_meal__title')
    ordering = ('-reservation_date',)
    raw_id_fields = ('host_user', 'daily_menu', 'meal_option')
    
    def jalali_date(self, obj):
        if obj.daily_menu and obj.daily_menu.date:
            return date2jalali(obj.daily_menu.date).strftime('%Y/%m/%d')
        return '-'
    jalali_date.short_description = 'تاریخ شمسی'
    jalali_date.admin_order_field = 'daily_menu__date'
    
    def get_meal_option_title(self, obj):
        if obj.meal_option:
            return f"{obj.meal_option.base_meal.title} - {obj.meal_option.title}"
        return "بدون غذا"
    get_meal_option_title.short_description = 'گزینه غذا'
    get_meal_option_title.admin_order_field = 'meal_option__title'
    
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


