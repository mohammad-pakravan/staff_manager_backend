from django.contrib import admin
from django.utils.html import format_html
from django.urls import path
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from jalali_date.admin import ModelAdminJalaliMixin
from jalali_date import datetime2jalali, date2jalali
from .models import (
    Restaurant, BaseMeal, DailyMenu, DailyMenuMealOption,
    FoodReservation, FoodReport, GuestReservation,
    Dessert, DessertReservation, GuestDessertReservation
)
# برای سازگاری با کدهای قبلی
Meal = BaseMeal


@admin.register(Restaurant)
class RestaurantAdmin(ModelAdminJalaliMixin, admin.ModelAdmin):
    list_display = ('name', 'get_centers_display', 'is_active', 'jalali_created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name',)
    ordering = ('name',)
    filter_horizontal = ('centers',)
    
    def get_centers_display(self, obj):
        """نمایش مراکز"""
        try:
            return ', '.join([c.name for c in obj.centers.all()])
        except Exception:
            return '-'
    get_centers_display.short_description = 'مراکز'
    
    def jalali_created_at(self, obj):
        if obj.created_at:
            return datetime2jalali(obj.created_at).strftime('%Y/%m/%d %H:%M')
        return '-'
    jalali_created_at.short_description = 'تاریخ ایجاد (شمسی)'
    jalali_created_at.admin_order_field = 'created_at'


@admin.register(BaseMeal)
class BaseMealAdmin(ModelAdminJalaliMixin, admin.ModelAdmin):
    list_display = ('title', 'restaurant', 'options_count', 'jalali_created_at', 'is_active', 'image_preview')
    list_filter = ('restaurant', 'is_active', 'created_at')
    search_fields = ('title', 'description', 'ingredients')
    ordering = ('title',)
    raw_id_fields = ('restaurant',)
    fieldsets = (
        ('اطلاعات پایه', {
            'fields': ('title', 'description', 'ingredients', 'image', 'restaurant', 'is_active')
        }),
    )
    
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
                return cleaned_data
        
        kwargs['form'] = BaseMealAdminForm
        return super().get_form(request, obj, **kwargs)
    
    def save_model(self, request, obj, form, change):
        """ذخیره مدل"""
        super().save_model(request, obj, form, change)
    
    def options_count(self, obj):
        """تعداد meal options مرتبط با این base meal در تمام daily menus"""
        from .models import DailyMenuMealOption
        return DailyMenuMealOption.objects.filter(base_meal=obj).count()
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


# MealOption حذف شد - فقط DailyMenuMealOption استفاده می‌شود


# برای سازگاری با کدهای قبلی
MealAdmin = BaseMealAdmin


@admin.register(Dessert)
class DessertAdmin(ModelAdminJalaliMixin, admin.ModelAdmin):
    list_display = ('title', 'center', 'restaurant', 'jalali_created_at', 'is_active', 'image_preview')
    list_filter = ('center', 'restaurant', 'is_active', 'created_at')
    search_fields = ('title', 'description', 'ingredients')
    ordering = ('title',)
    raw_id_fields = ('restaurant',)
    fieldsets = (
        ('اطلاعات پایه', {
            'fields': ('title', 'description', 'ingredients', 'image', 'restaurant', 'is_active')
        }),
    )
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'restaurant':
            kwargs['queryset'] = Restaurant.objects.filter(is_active=True)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
    
    def get_form(self, request, obj=None, **kwargs):
        from django import forms
        from .models import Dessert
        
        class DessertAdminForm(forms.ModelForm):
            class Meta:
                model = Dessert
                fields = '__all__'
            
            def clean(self):
                cleaned_data = super().clean()
                restaurant = cleaned_data.get('restaurant')
                
                try:
                    if restaurant and restaurant.centers.exists():
                        cleaned_data['center'] = restaurant.centers.first()
                except Exception:
                    pass
                
                return cleaned_data
        
        kwargs['form'] = DessertAdminForm
        return super().get_form(request, obj, **kwargs)
    
    def save_model(self, request, obj, form, change):
        try:
            if obj.restaurant and obj.restaurant.centers.exists():
                obj.center = obj.restaurant.centers.first()
        except Exception:
            pass
        super().save_model(request, obj, form, change)
    
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




@admin.register(DailyMenu)
class DailyMenuAdmin(ModelAdminJalaliMixin, admin.ModelAdmin):
    list_display = (
        'restaurant', 'get_center_display', 'jalali_date', 'meal_options_count', 
        'max_reservations_per_meal', 'is_available'
    )
    list_filter = ('date', 'is_available', 'restaurant')  # 'restaurant__centers' temporarily removed until migration is applied
    search_fields = ('restaurant__name',)  # 'restaurant__centers__name' temporarily removed until migration is applied
    ordering = ('-date',)
    raw_id_fields = ('restaurant',)
    filter_horizontal = ('base_meals', 'desserts')
    change_form_template = 'admin/food_management/dailymenu/change_form.html'
    add_form_template = 'admin/food_management/dailymenu/change_form.html'
    
    def get_center_display(self, obj):
        """نمایش مراکز از طریق رستوران"""
        try:
            if obj.restaurant and obj.restaurant.centers.exists():
                return ', '.join([c.name for c in obj.restaurant.centers.all()])
        except Exception:
            pass
        return '-'
    get_center_display.short_description = 'مراکز'
    
    def formfield_for_manytomany(self, db_field, request, **kwargs):
        """فیلتر کردن base_meals و desserts بر اساس رستوران"""
        if db_field.name == 'base_meals':
            from .models import BaseMeal
            
            # اگر در حال ویرایش یک DailyMenu هستیم
            if hasattr(request, 'resolver_match') and request.resolver_match:
                try:
                    daily_menu_id = request.resolver_match.kwargs.get('object_id')
                    if daily_menu_id:
                        try:
                            daily_menu = DailyMenu.objects.get(pk=daily_menu_id)
                            if daily_menu.restaurant:
                                kwargs['queryset'] = BaseMeal.objects.filter(
                                    restaurant=daily_menu.restaurant,
                                    is_active=True
                                )
                        except DailyMenu.DoesNotExist:
                            pass
                except Exception:
                    pass
            
            # اگر در حال ایجاد DailyMenu جدید هستیم و restaurant از POST آمده
            if not kwargs.get('queryset'):
                restaurant_id = request.POST.get('restaurant')
                if restaurant_id:
                    try:
                        restaurant = Restaurant.objects.get(pk=restaurant_id)
                        kwargs['queryset'] = BaseMeal.objects.filter(
                            restaurant=restaurant,
                            is_active=True
                        )
                    except (Restaurant.DoesNotExist, ValueError, TypeError):
                        pass
        
        elif db_field.name == 'desserts':
            # اگر در حال ویرایش یک DailyMenu هستیم
            if hasattr(request, 'resolver_match') and request.resolver_match:
                try:
                    daily_menu_id = request.resolver_match.kwargs.get('object_id')
                    if daily_menu_id:
                        try:
                            daily_menu = DailyMenu.objects.get(pk=daily_menu_id)
                            if daily_menu.restaurant:
                                kwargs['queryset'] = Dessert.objects.filter(
                                    restaurant=daily_menu.restaurant,
                                    is_active=True
                                )
                        except DailyMenu.DoesNotExist:
                            pass
                except Exception:
                    pass
            
            # اگر در حال ایجاد DailyMenu جدید هستیم و restaurant از POST آمده
            if not kwargs.get('queryset'):
                restaurant_id = request.POST.get('restaurant')
                if restaurant_id:
                    try:
                        restaurant = Restaurant.objects.get(pk=restaurant_id)
                        kwargs['queryset'] = Dessert.objects.filter(
                            restaurant=restaurant,
                            is_active=True
                        )
                    except (Restaurant.DoesNotExist, ValueError, TypeError):
                        pass
        
        return super().formfield_for_manytomany(db_field, request, **kwargs)
    
    def get_urls(self):
        """افزودن URL برای دریافت base_meals و مدیریت meal options"""
        urls = super().get_urls()
        custom_urls = [
            path('base-meals-by-restaurant/', self.admin_site.admin_view(self.get_base_meals_by_restaurant), name='food_management_dailymenu_base_meals_by_restaurant'),
            path('<int:object_id>/meal-options/', self.admin_site.admin_view(self.get_meal_options), name='food_management_dailymenu_meal_options'),
            path('<int:object_id>/meal-options/create/', self.admin_site.admin_view(self.create_meal_option), name='food_management_dailymenu_meal_option_create'),
            path('<int:object_id>/meal-options/<int:option_id>/update/', self.admin_site.admin_view(self.update_meal_option), name='food_management_dailymenu_meal_option_update'),
            path('<int:object_id>/meal-options/<int:option_id>/delete/', self.admin_site.admin_view(self.delete_meal_option), name='food_management_dailymenu_meal_option_delete'),
        ]
        return custom_urls + urls
    
    def get_base_meals_by_restaurant(self, request):
        """API endpoint برای دریافت base_meals بر اساس restaurant_id"""
        restaurant_id = request.GET.get('restaurant_id')
        if not restaurant_id:
            return JsonResponse({'error': 'restaurant_id required'}, status=400)
        
        try:
            from .models import BaseMeal
            restaurant = Restaurant.objects.get(pk=restaurant_id)
            base_meals = BaseMeal.objects.filter(
                restaurant=restaurant,
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
        except Restaurant.DoesNotExist:
            return JsonResponse({'error': 'Restaurant not found'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    def get_meal_options(self, request, object_id):
        """دریافت لیست اپشن‌های غذا برای یک منو"""
        try:
            daily_menu = DailyMenu.objects.get(pk=object_id)
            meal_options = DailyMenuMealOption.objects.filter(daily_menu=daily_menu).select_related('base_meal').order_by('title')
            
            from django.utils import timezone
            options_data = [
                {
                    'id': option.id,
                    'base_meal_id': option.base_meal.id,
                    'base_meal_title': option.base_meal.title,
                    'title': option.title,
                    'description': option.description or '',
                    'price': str(option.price),
                    'quantity': option.quantity,
                    'reserved_quantity': option.reserved_quantity,
                    'is_default': option.is_default,
                    'cancellation_deadline': option.cancellation_deadline.strftime('%Y-%m-%dT%H:%M') if option.cancellation_deadline else '',
                }
                for option in meal_options
            ]
            
            return JsonResponse({'options': options_data})
        except DailyMenu.DoesNotExist:
            return JsonResponse({'error': 'DailyMenu not found'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    def create_meal_option(self, request, object_id):
        """ایجاد اپشن غذا جدید برای منو"""
        if request.method != 'POST':
            return JsonResponse({'error': 'Method not allowed'}, status=405)
        
        try:
            # object_id is already an int from URL pattern
            daily_menu = DailyMenu.objects.get(pk=object_id)
            base_meal_id = request.POST.get('base_meal_id')
            title = request.POST.get('title')
            description = request.POST.get('description', '')
            price = request.POST.get('price', '0')
            quantity = request.POST.get('quantity', '0')
            is_default = False  # Always False, field removed from form
            cancellation_deadline = request.POST.get('cancellation_deadline', '')
            
            if not base_meal_id:
                return JsonResponse({'error': 'base_meal_id الزامی است'}, status=400)
            if not title or not title.strip():
                return JsonResponse({'error': 'عنوان اپشن الزامی است'}, status=400)
            
            try:
                base_meal = BaseMeal.objects.get(pk=base_meal_id)
            except BaseMeal.DoesNotExist:
                return JsonResponse({'error': 'غذای پایه پیدا نشد'}, status=404)
            
            # Validate price
            try:
                price_decimal = float(price)
                if price_decimal < 0:
                    return JsonResponse({'error': 'قیمت نمی‌تواند منفی باشد'}, status=400)
                # DecimalField(max_digits=10, decimal_places=2) max value is 99999999.99
                if price_decimal > 99999999.99:
                    return JsonResponse({'error': 'قیمت نمی‌تواند بیشتر از 99,999,999.99 باشد'}, status=400)
            except (ValueError, TypeError):
                return JsonResponse({'error': 'قیمت نامعتبر است'}, status=400)
            
            # Validate quantity
            try:
                quantity_int = int(quantity)
                if quantity_int < 0:
                    return JsonResponse({'error': 'تعداد نمی‌تواند منفی باشد'}, status=400)
                # PositiveIntegerField max value is 2147483647
                if quantity_int > 2147483647:
                    return JsonResponse({'error': 'تعداد نمی‌تواند بیشتر از 2,147,483,647 باشد'}, status=400)
            except (ValueError, TypeError):
                return JsonResponse({'error': 'تعداد نامعتبر است'}, status=400)
            except OverflowError:
                return JsonResponse({'error': 'تعداد خیلی بزرگ است'}, status=400)
            
            from django.utils.dateparse import parse_datetime
            from django.utils import timezone
            
            # Parse cancellation_deadline
            cancellation_deadline_dt = None
            if cancellation_deadline:
                try:
                    cancellation_deadline_dt = parse_datetime(cancellation_deadline)
                    if cancellation_deadline_dt and not timezone.is_aware(cancellation_deadline_dt):
                        cancellation_deadline_dt = timezone.make_aware(cancellation_deadline_dt)
                except (ValueError, TypeError):
                    pass
            
            try:
                meal_option = DailyMenuMealOption.objects.create(
                    daily_menu=daily_menu,
                    base_meal=base_meal,
                    title=title.strip(),
                    description=description.strip() if description else '',
                    price=price_decimal,
                    quantity=quantity_int,
                    is_default=is_default,
                    cancellation_deadline=cancellation_deadline_dt,
                    sort_order=0
                )
            except Exception as e:
                # Catch database errors like numeric field overflow
                error_msg = str(e)
                if 'numeric field overflow' in error_msg.lower() or 'overflow' in error_msg.lower():
                    return JsonResponse({
                        'error': 'مقدار عددی خیلی بزرگ است. لطفاً مقادیر را کاهش دهید.',
                        'details': error_msg
                    }, status=400)
                raise
            
            return JsonResponse({
                'success': True,
                'option': {
                    'id': meal_option.id,
                    'base_meal_id': meal_option.base_meal.id,
                    'base_meal_title': meal_option.base_meal.title,
                    'title': meal_option.title,
                    'description': meal_option.description or '',
                    'price': str(meal_option.price),
                    'quantity': meal_option.quantity,
                    'is_default': meal_option.is_default,
                    'cancellation_deadline': meal_option.cancellation_deadline.strftime('%Y-%m-%dT%H:%M') if meal_option.cancellation_deadline else '',
                }
            })
        except DailyMenu.DoesNotExist:
            return JsonResponse({'error': 'منوی روزانه پیدا نشد'}, status=404)
        except ValueError as e:
            import traceback
            return JsonResponse({
                'error': f'مقدار نامعتبر: {str(e)}',
                'traceback': traceback.format_exc()
            }, status=400)
        except Exception as e:
            import traceback
            error_traceback = traceback.format_exc()
            print(f"Error in create_meal_option: {str(e)}")
            print(f"Traceback: {error_traceback}")
            return JsonResponse({
                'error': f'خطای سرور: {str(e)}',
                'traceback': error_traceback
            }, status=500)
    
    def update_meal_option(self, request, object_id, option_id):
        """ویرایش اپشن غذا"""
        if request.method != 'POST':
            return JsonResponse({'error': 'Method not allowed'}, status=405)
        
        try:
            # object_id is already an int from URL pattern
            daily_menu = DailyMenu.objects.get(pk=object_id)
            meal_option = DailyMenuMealOption.objects.get(pk=option_id, daily_menu=daily_menu)
            
            if 'title' in request.POST:
                title = request.POST.get('title', '').strip()
                if not title:
                    return JsonResponse({'error': 'عنوان اپشن الزامی است'}, status=400)
                meal_option.title = title
            
            if 'description' in request.POST:
                meal_option.description = request.POST.get('description', '').strip()
            
            if 'price' in request.POST:
                try:
                    price_decimal = float(request.POST.get('price', '0'))
                    if price_decimal < 0:
                        return JsonResponse({'error': 'قیمت نمی‌تواند منفی باشد'}, status=400)
                    # DecimalField(max_digits=10, decimal_places=2) max value is 99999999.99
                    if price_decimal > 99999999.99:
                        return JsonResponse({'error': 'قیمت نمی‌تواند بیشتر از 99,999,999.99 باشد'}, status=400)
                    meal_option.price = price_decimal
                except (ValueError, TypeError):
                    return JsonResponse({'error': 'قیمت نامعتبر است'}, status=400)
                except OverflowError:
                    return JsonResponse({'error': 'قیمت خیلی بزرگ است'}, status=400)
            
            if 'quantity' in request.POST:
                try:
                    quantity_int = int(request.POST.get('quantity', '0'))
                    if quantity_int < 0:
                        return JsonResponse({'error': 'تعداد نمی‌تواند منفی باشد'}, status=400)
                    # PositiveIntegerField max value is 2147483647
                    if quantity_int > 2147483647:
                        return JsonResponse({'error': 'تعداد نمی‌تواند بیشتر از 2,147,483,647 باشد'}, status=400)
                    meal_option.quantity = quantity_int
                except (ValueError, TypeError):
                    return JsonResponse({'error': 'تعداد نامعتبر است'}, status=400)
                except OverflowError:
                    return JsonResponse({'error': 'تعداد خیلی بزرگ است'}, status=400)
            
            # is_default field removed from form, always keep False
            meal_option.is_default = False
            
            if 'cancellation_deadline' in request.POST:
                from django.utils.dateparse import parse_datetime
                from django.utils import timezone
                cancellation_deadline = request.POST.get('cancellation_deadline', '')
                if cancellation_deadline:
                    try:
                        cancellation_deadline_dt = parse_datetime(cancellation_deadline)
                        if cancellation_deadline_dt and not timezone.is_aware(cancellation_deadline_dt):
                            cancellation_deadline_dt = timezone.make_aware(cancellation_deadline_dt)
                        meal_option.cancellation_deadline = cancellation_deadline_dt
                    except (ValueError, TypeError):
                        pass
                else:
                    meal_option.cancellation_deadline = None
            
            # sort_order field removed from form, always keep 0
            meal_option.sort_order = 0
            
            try:
                meal_option.save()
            except Exception as e:
                # Catch database errors like numeric field overflow
                error_msg = str(e)
                if 'numeric field overflow' in error_msg.lower() or 'overflow' in error_msg.lower():
                    return JsonResponse({
                        'error': 'مقدار عددی خیلی بزرگ است. لطفاً مقادیر را کاهش دهید.',
                        'details': error_msg
                    }, status=400)
                raise
            
            return JsonResponse({
                'success': True,
                'option': {
                    'id': meal_option.id,
                    'base_meal_id': meal_option.base_meal.id,
                    'base_meal_title': meal_option.base_meal.title,
                    'title': meal_option.title,
                    'description': meal_option.description or '',
                    'price': str(meal_option.price),
                    'quantity': meal_option.quantity,
                    'is_default': meal_option.is_default,
                    'cancellation_deadline': meal_option.cancellation_deadline.strftime('%Y-%m-%dT%H:%M') if meal_option.cancellation_deadline else '',
                }
            })
        except DailyMenu.DoesNotExist:
            return JsonResponse({'error': 'منوی روزانه پیدا نشد'}, status=404)
        except DailyMenuMealOption.DoesNotExist:
            return JsonResponse({'error': 'اپشن غذا پیدا نشد'}, status=404)
        except ValueError as e:
            import traceback
            error_traceback = traceback.format_exc()
            print(f"ValueError in update_meal_option: {str(e)}")
            print(f"Traceback: {error_traceback}")
            return JsonResponse({
                'error': f'مقدار نامعتبر: {str(e)}',
                'traceback': error_traceback
            }, status=400)
        except Exception as e:
            import traceback
            error_traceback = traceback.format_exc()
            print(f"Error in update_meal_option: {str(e)}")
            print(f"Traceback: {error_traceback}")
            return JsonResponse({
                'error': f'خطای سرور: {str(e)}',
                'traceback': error_traceback
            }, status=500)
    
    def delete_meal_option(self, request, object_id, option_id):
        """حذف اپشن غذا"""
        if request.method != 'POST':
            return JsonResponse({'error': 'Method not allowed'}, status=405)
        
        try:
            # object_id is already an int from URL pattern
            daily_menu = DailyMenu.objects.get(pk=object_id)
            meal_option = DailyMenuMealOption.objects.get(pk=option_id, daily_menu=daily_menu)
            meal_option.delete()
            
            return JsonResponse({'success': True})
        except DailyMenu.DoesNotExist:
            return JsonResponse({'error': 'DailyMenu not found'}, status=404)
        except DailyMenuMealOption.DoesNotExist:
            return JsonResponse({'error': 'MealOption not found'}, status=404)
        except ValueError as e:
            return JsonResponse({'error': f'Invalid ID: {str(e)}'}, status=400)
        except Exception as e:
            import traceback
            return JsonResponse({'error': str(e), 'traceback': traceback.format_exc()}, status=500)
    
    def get_form(self, request, obj=None, **kwargs):
        """تنظیم queryset base_meals بر اساس رستوران"""
        form = super().get_form(request, obj, **kwargs)
        
        # اگر در حال ویرایش هستیم و restaurant وجود دارد
        if obj and obj.restaurant:
            from .models import BaseMeal
            if 'base_meals' in form.base_fields:
                form.base_fields['base_meals'].queryset = BaseMeal.objects.filter(
                    restaurant=obj.restaurant,
                    is_active=True
                )
        else:
            # اگر در حال ایجاد هستیم، فقط base_meals فعال را نشان بده
            # کاربر باید ابتدا restaurant را انتخاب کند، سپس صفحه را refresh کند
            from .models import BaseMeal
            if 'base_meals' in form.base_fields:
                form.base_fields['base_meals'].queryset = BaseMeal.objects.filter(
                    is_active=True
                )
        
        return form
    
    
    def save_model(self, request, obj, form, change):
        """ذخیره مدل"""
        super().save_model(request, obj, form, change)
    
    def render_change_form(self, request, context, *args, **kwargs):
        """رندر کردن فرم تغییر با template سفارشی"""
        return super().render_change_form(request, context, *args, **kwargs)
    
    def jalali_date(self, obj):
        if obj.date:
            return date2jalali(obj.date).strftime('%Y/%m/%d')
        return '-'
    jalali_date.short_description = 'تاریخ شمسی'
    jalali_date.admin_order_field = 'date'
    
    def meal_options_count(self, obj):
        if obj.pk:
            return DailyMenuMealOption.objects.filter(daily_menu=obj).count()
        return 0
    meal_options_count.short_description = 'تعداد غذاها'




@admin.register(FoodReservation)
class FoodReservationAdmin(ModelAdminJalaliMixin, admin.ModelAdmin):
    list_display = (
        'user', 'jalali_date', 'get_meal_option_title', 'quantity', 'status', 'amount', 
        'jalali_reservation_date', 'jalali_cancellation_deadline', 'can_cancel_status'
    )
    list_filter = ('status', 'reservation_date')  # 'daily_menu__restaurant__centers' temporarily removed until migration is applied
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
    list_filter = ('status', 'reservation_date')  # 'daily_menu__restaurant__centers' temporarily removed until migration is applied
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


@admin.register(DessertReservation)
class DessertReservationAdmin(ModelAdminJalaliMixin, admin.ModelAdmin):
    list_display = (
        'user', 'jalali_date', 'get_dessert_title', 'quantity', 'status', 'amount', 
        'jalali_reservation_date', 'jalali_cancellation_deadline', 'can_cancel_status'
    )
    list_filter = ('status', 'reservation_date')
    search_fields = ('user__username', 'user__employee_number', 'dessert__title', 'dessert__dessert__title', 'daily_menu_info', 'dessert_info')
    ordering = ('-reservation_date',)
    raw_id_fields = ('user', 'daily_menu', 'dessert')
    readonly_fields = ('daily_menu_info', 'dessert_info', 'reservation_date')
    fieldsets = (
        ('اطلاعات رزرو', {
            'fields': ('user', 'daily_menu', 'daily_menu_info', 'dessert', 'dessert_info', 'quantity', 'status', 'amount')
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
    
    def get_dessert_title(self, obj):
        if obj.dessert:
            return obj.dessert.title
        elif obj.dessert_info:
            return obj.dessert_info
        return "بدون دسر"
    get_dessert_title.short_description = 'دسر'
    get_dessert_title.admin_order_field = 'dessert__title'
    
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


@admin.register(GuestDessertReservation)
class GuestDessertReservationAdmin(ModelAdminJalaliMixin, admin.ModelAdmin):
    list_display = (
        'guest_first_name', 'guest_last_name', 'host_user', 'jalali_date', 'get_dessert_title', 
        'status', 'amount', 'jalali_reservation_date', 'jalali_cancellation_deadline', 'can_cancel_status'
    )
    list_filter = ('status', 'reservation_date')
    search_fields = ('guest_first_name', 'guest_last_name', 'host_user__username', 'host_user__employee_number', 'dessert__title', 'dessert__dessert__title', 'daily_menu_info', 'dessert_info')
    ordering = ('-reservation_date',)
    raw_id_fields = ('host_user', 'daily_menu', 'dessert')
    readonly_fields = ('daily_menu_info', 'dessert_info', 'reservation_date')
    fieldsets = (
        ('اطلاعات رزرو', {
            'fields': ('host_user', 'guest_first_name', 'guest_last_name', 'daily_menu', 'daily_menu_info', 'dessert', 'dessert_info', 'status', 'amount')
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
    
    def get_dessert_title(self, obj):
        if obj.dessert:
            return obj.dessert.title
        elif obj.dessert_info:
            return obj.dessert_info
        return "بدون دسر"
    get_dessert_title.short_description = 'دسر'
    get_dessert_title.admin_order_field = 'dessert__title'
    
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


