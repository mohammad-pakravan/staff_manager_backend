from django.contrib import admin
from django.utils.html import format_html
from django.urls import path
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from jalali_date.admin import ModelAdminJalaliMixin
from jalali_date import datetime2jalali, date2jalali
from .models import (
    Restaurant, BaseMeal, MealOption, DailyMenu, 
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
    list_display = ('title', 'center', 'restaurant', 'jalali_cancellation_deadline', 'options_count', 'jalali_created_at', 'is_active', 'image_preview')
    list_filter = ('center', 'restaurant', 'is_active', 'created_at', 'cancellation_deadline')
    search_fields = ('title', 'description')
    ordering = ('title',)
    raw_id_fields = ('restaurant',)
    fieldsets = (
        ('اطلاعات پایه', {
            'fields': ('title', 'description', 'image', 'restaurant', 'is_active')
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
        """فیلتر کردن رستوران‌های فعال"""
        if db_field.name == 'restaurant':
            # فقط رستوران‌های فعال را نمایش بده
            kwargs['queryset'] = Restaurant.objects.filter(is_active=True)
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
                
                # تنظیم خودکار مرکز از رستوران
                if restaurant and restaurant.center:
                    cleaned_data['center'] = restaurant.center
                
                return cleaned_data
        
        kwargs['form'] = BaseMealAdminForm
        return super().get_form(request, obj, **kwargs)
    
    def save_model(self, request, obj, form, change):
        """ذخیره مدل و تنظیم خودکار مرکز از رستوران"""
        # اگر رستوران انتخاب شده، مرکز را از رستوران بگیر
        if obj.restaurant and obj.restaurant.center:
            obj.center = obj.restaurant.center
        super().save_model(request, obj, form, change)
    
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




@admin.register(DailyMenu)
class DailyMenuAdmin(ModelAdminJalaliMixin, admin.ModelAdmin):
    list_display = (
        'center', 'jalali_date', 'meal_options_count', 
        'max_reservations_per_meal', 'is_available'
    )
    list_filter = ('date', 'is_available', 'center')
    search_fields = ('center__name',)
    ordering = ('-date',)
    raw_id_fields = ('center',)
    filter_horizontal = ('base_meals',)
    exclude = ('meal_options',)  # مخفی کردن meal_options چون از base_meals ساخته می‌شود
    change_form_template = 'admin/food_management/dailymenu/change_form.html'
    add_form_template = 'admin/food_management/dailymenu/change_form.html'
    
    def formfield_for_manytomany(self, db_field, request, **kwargs):
        """فیلتر کردن base_meals بر اساس مرکز"""
        if db_field.name == 'base_meals':
            from .models import BaseMeal
            
            # اگر در حال ویرایش یک DailyMenu هستیم
            if hasattr(request, 'resolver_match') and request.resolver_match:
                try:
                    daily_menu_id = request.resolver_match.kwargs.get('object_id')
                    if daily_menu_id:
                        try:
                            daily_menu = DailyMenu.objects.get(pk=daily_menu_id)
                            if daily_menu.center:
                                kwargs['queryset'] = BaseMeal.objects.filter(
                                    center=daily_menu.center,
                                    is_active=True
                                )
                        except DailyMenu.DoesNotExist:
                            pass
                except Exception:
                    pass
            
            # اگر در حال ایجاد DailyMenu جدید هستیم و center از POST آمده
            if not kwargs.get('queryset'):
                center_id = request.POST.get('center')
                if center_id:
                    try:
                        from apps.centers.models import Center
                        center = Center.objects.get(pk=center_id)
                        kwargs['queryset'] = BaseMeal.objects.filter(
                            center=center,
                            is_active=True
                        )
                    except (Center.DoesNotExist, ValueError, TypeError):
                        pass
        
        return super().formfield_for_manytomany(db_field, request, **kwargs)
    
    def get_urls(self):
        """افزودن URL برای دریافت base_meals بر اساس center"""
        urls = super().get_urls()
        custom_urls = [
            path('base-meals-by-center/', self.admin_site.admin_view(self.get_base_meals_by_center), name='food_management_dailymenu_base_meals_by_center'),
        ]
        return custom_urls + urls
    
    def get_base_meals_by_center(self, request):
        """API endpoint برای دریافت base_meals بر اساس center_id"""
        center_id = request.GET.get('center_id')
        if not center_id:
            return JsonResponse({'error': 'center_id required'}, status=400)
        
        try:
            from apps.centers.models import Center
            from .models import BaseMeal
            center = Center.objects.get(pk=center_id)
            base_meals = BaseMeal.objects.filter(
                center=center,
                is_active=True
            ).order_by('title')
            
            options_data = [
                {
                    'id': base_meal.id,
                    'text': base_meal.title,
                    'title': base_meal.title
                }
                for base_meal in base_meals
            ]
            
            return JsonResponse({'options': options_data})
        except Center.DoesNotExist:
            return JsonResponse({'error': 'Center not found'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    def get_form(self, request, obj=None, **kwargs):
        """تنظیم queryset base_meals بر اساس مرکز"""
        form = super().get_form(request, obj, **kwargs)
        
        # اگر در حال ویرایش هستیم و center وجود دارد
        if obj and obj.center:
            from .models import BaseMeal
            if 'base_meals' in form.base_fields:
                form.base_fields['base_meals'].queryset = BaseMeal.objects.filter(
                    center=obj.center,
                    is_active=True
                )
        else:
            # اگر در حال ایجاد هستیم، فقط base_meals فعال را نشان بده
            # کاربر باید ابتدا center را انتخاب کند، سپس صفحه را refresh کند
            from .models import BaseMeal
            if 'base_meals' in form.base_fields:
                form.base_fields['base_meals'].queryset = BaseMeal.objects.filter(
                    is_active=True
                )
        
        return form
    
    
    def save_model(self, request, obj, form, change):
        """ذخیره مدل و همگام‌سازی meal_options از base_meals"""
        super().save_model(request, obj, form, change)
        
        # همگام‌سازی meal_options از base_meals
        if obj.base_meals.exists():
            obj.sync_meal_options_from_base_meals()
        
        # بررسی اینکه همه meal_options مربوط به center هستند
        if obj.center:
            from .models import MealOption
            invalid_options = obj.meal_options.exclude(base_meal__center=obj.center)
            if invalid_options.exists():
                # حذف meal_options نامعتبر
                obj.meal_options.remove(*invalid_options)
                from django.contrib import messages
                messages.warning(
                    request,
                    f'توجه: {invalid_options.count()} غذای نامعتبر (مربوط به مرکز دیگر) از منو حذف شد.'
                )
    
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
    list_filter = ('status', 'reservation_date', 'daily_menu__center')
    search_fields = ('user__username', 'user__employee_number', 'meal_option__title', 'meal_option__base_meal__title', 'daily_menu_info', 'meal_option_info')
    ordering = ('-reservation_date',)
    raw_id_fields = ('user', 'daily_menu', 'meal_option')
    readonly_fields = ('daily_menu_info', 'meal_option_info', 'reservation_date')
    fieldsets = (
        ('اطلاعات رزرو', {
            'fields': ('user', 'daily_menu', 'daily_menu_info', 'meal_option', 'meal_option_info', 'quantity', 'status', 'amount')
        }),
        ('تاریخ‌ها', {
            'fields': ('reservation_date', 'cancellation_deadline', 'cancelled_at')
        }),
    )
    
    def jalali_date(self, obj):
        if obj.daily_menu and obj.daily_menu.date:
            return date2jalali(obj.daily_menu.date).strftime('%Y/%m/%d')
        elif obj.daily_menu_info:
            return obj.daily_menu_info
        return '-'
    jalali_date.short_description = 'تاریخ شمسی'
    jalali_date.admin_order_field = 'daily_menu__date'
    
    def get_meal_option_title(self, obj):
        if obj.meal_option:
            return f"{obj.meal_option.base_meal.title} - {obj.meal_option.title}"
        elif obj.meal_option_info:
            return obj.meal_option_info
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
    list_filter = ('status', 'reservation_date', 'daily_menu__center')
    search_fields = ('guest_first_name', 'guest_last_name', 'host_user__username', 'host_user__employee_number', 'meal_option__title', 'meal_option__base_meal__title', 'daily_menu_info', 'meal_option_info')
    ordering = ('-reservation_date',)
    raw_id_fields = ('host_user', 'daily_menu', 'meal_option')
    readonly_fields = ('daily_menu_info', 'meal_option_info', 'reservation_date')
    fieldsets = (
        ('اطلاعات رزرو', {
            'fields': ('host_user', 'guest_first_name', 'guest_last_name', 'daily_menu', 'daily_menu_info', 'meal_option', 'meal_option_info', 'status', 'amount')
        }),
        ('تاریخ‌ها', {
            'fields': ('reservation_date', 'cancellation_deadline', 'cancelled_at')
        }),
    )
    
    def jalali_date(self, obj):
        if obj.daily_menu and obj.daily_menu.date:
            return date2jalali(obj.daily_menu.date).strftime('%Y/%m/%d')
        elif obj.daily_menu_info:
            return obj.daily_menu_info
        return '-'
    jalali_date.short_description = 'تاریخ شمسی'
    jalali_date.admin_order_field = 'daily_menu__date'
    
    def get_meal_option_title(self, obj):
        if obj.meal_option:
            return f"{obj.meal_option.base_meal.title} - {obj.meal_option.title}"
        elif obj.meal_option_info:
            return obj.meal_option_info
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


