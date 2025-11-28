"""
Serializers for meals app
"""
from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from datetime import datetime
from jalali_date import datetime2jalali, date2jalali
from apps.food_management.models import (
    Restaurant, BaseMeal, DailyMenu, DailyMenuMealOption,
    BaseDessert, DailyMenuDessertOption
)
# برای سازگاری با کدهای قبلی
Dessert = BaseDessert
from apps.centers.models import Center
# برای سازگاری با کدهای قبلی
Meal = BaseMeal


class CenterSerializer(serializers.ModelSerializer):
    """سریالایزر مرکز"""
    class Meta:
        model = Center
        fields = ['id', 'name']


class CenterMenuSerializer(serializers.ModelSerializer):
    """سریالایزر ساده مرکز برای منو - فقط id, name, logo_url"""
    logo_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Center
        fields = ['id', 'name', 'logo_url']
    
    @extend_schema_field(serializers.CharField())
    def get_logo_url(self, obj):
        """URL لوگو مرکز"""
        if obj.logo:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.logo.url)
            return obj.logo.url
        return None


class RestaurantSerializer(serializers.ModelSerializer):
    """سریالایزر رستوران"""
    centers = serializers.SerializerMethodField(read_only=True)  # لیست جزئیات مراکز برای خواندن
    jalali_created_at = serializers.SerializerMethodField()
    jalali_updated_at = serializers.SerializerMethodField()
    
    class Meta:
        model = Restaurant
        fields = [
            'id', 'name', 'centers', 'is_active', 'created_at', 'jalali_created_at', 
            'updated_at', 'jalali_updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def __init__(self, *args, **kwargs):
        # بررسی اینکه آیا در حالت نوشتن هستیم (data وجود دارد)
        is_writing = 'data' in kwargs
        super().__init__(*args, **kwargs)
        
        # برای نوشتن: فیلد centers را به PrimaryKeyRelatedField تبدیل می‌کنیم
        if is_writing and 'centers' in self.fields:
            # حذف SerializerMethodField
            del self.fields['centers']
            # اضافه کردن PrimaryKeyRelatedField
            self.fields['centers'] = serializers.PrimaryKeyRelatedField(
                many=True,
                queryset=Center.objects.all(),
                required=False,
                allow_empty=True
            )
    
    @extend_schema_field(serializers.ListField(child=CenterSerializer()))
    def get_centers(self, obj):
        """برگرداندن لیست جزئیات مراکز"""
        centers = obj.centers.all()
        if centers.exists():
            return CenterSerializer(centers, many=True).data
        return []
    
    def create(self, validated_data):
        """ایجاد رستوران با مراکز"""
        centers = validated_data.pop('centers', [])
        restaurant = Restaurant.objects.create(**validated_data)
        if centers:
            # تبدیل به لیست در صورت نیاز
            if hasattr(centers, '__iter__') and not isinstance(centers, (str, bytes)):
                centers_list = list(centers) if centers else []
            else:
                centers_list = [centers] if centers else []
            
            if centers_list:
                restaurant.centers.set(centers_list)
        return restaurant
    
    def update(self, instance, validated_data):
        """به‌روزرسانی رستوران با مراکز"""
        centers = validated_data.pop('centers', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if centers is not None:
            # تبدیل به لیست در صورت نیاز
            if hasattr(centers, '__iter__') and not isinstance(centers, (str, bytes)):
                centers_list = list(centers) if centers else []
            else:
                centers_list = [centers] if centers else []
            
            instance.centers.set(centers_list)
        return instance

    @extend_schema_field(serializers.CharField())
    def get_jalali_created_at(self, obj):
        if obj.created_at:
            return datetime2jalali(obj.created_at).strftime('%Y/%m/%d %H:%M')
        return None

    @extend_schema_field(serializers.CharField())
    def get_jalali_updated_at(self, obj):
        if obj.updated_at:
            return datetime2jalali(obj.updated_at).strftime('%Y/%m/%d %H:%M')
        return None


class SimpleRestaurantSerializer(serializers.ModelSerializer):
    """سریالایزر ساده برای رستوران - فقط اطلاعات ضروری"""
    centers = CenterSerializer(many=True, read_only=True)
    
    class Meta:
        model = Restaurant
        fields = [
            'id', 'name', 'centers', 'is_active'
        ]


class BaseMealSerializer(serializers.ModelSerializer):
    """سریالایزر غذای پایه"""
    restaurant_name = serializers.CharField(source='restaurant.name', read_only=True)
    restaurant_detail = RestaurantSerializer(source='restaurant', read_only=True)
    options = serializers.SerializerMethodField()
    jalali_created_at = serializers.SerializerMethodField()
    jalali_updated_at = serializers.SerializerMethodField()
    class Meta:
        model = BaseMeal
        fields = [
            'id', 'title', 'description', 'ingredients', 'image', 
            'restaurant', 'restaurant_name', 'restaurant_detail', 
            'is_active', 'options',
            'created_at', 'jalali_created_at', 'updated_at', 'jalali_updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # فیلتر کردن queryset رستوران‌ها - فقط رستوران‌های فعال
        if 'restaurant' in self.fields:
            self.fields['restaurant'].queryset = Restaurant.objects.filter(is_active=True)

    @extend_schema_field(serializers.ListField())
    def get_options(self, obj):
        """گزینه‌های غذا - حذف شد چون دیگر MealOption وجود ندارد"""
        # این متد دیگر استفاده نمی‌شود چون MealOption حذف شده
        return []

    @extend_schema_field(serializers.CharField())
    def get_jalali_created_at(self, obj):
        if obj.created_at:
            return datetime2jalali(obj.created_at).strftime('%Y/%m/%d %H:%M')
        return None

    @extend_schema_field(serializers.CharField())
    def get_jalali_updated_at(self, obj):
        if obj.updated_at:
            return datetime2jalali(obj.updated_at).strftime('%Y/%m/%d %H:%M')
        return None
    
    @extend_schema_field(serializers.CharField())
    def get_jalali_cancellation_deadline(self, obj):
        """مهلت لغو (به صورت string)"""
        if obj.cancellation_deadline:
            return str(obj.cancellation_deadline)
        return None
    
    def validate(self, data):
        """بررسی محدودیت رستوران"""
        restaurant = data.get('restaurant')
        
        # اگر از instance باشد (در زمان update)
        if not restaurant and self.instance:
            restaurant = self.instance.restaurant
        
        # رستوران باید انتخاب شود
        if not restaurant:
            raise serializers.ValidationError({
                'restaurant': 'رستوران باید انتخاب شود.'
            })
        
        return data


# برای سازگاری با کدهای قبلی
MealSerializer = BaseMealSerializer


class DailyMenuMealOptionSerializer(serializers.ModelSerializer):
    """سریالایزر برای DailyMenuMealOption"""
    base_meal_title = serializers.CharField(source='base_meal.title', read_only=True)
    base_meal_image = serializers.SerializerMethodField()
    restaurant_name = serializers.SerializerMethodField()
    restaurant_id = serializers.SerializerMethodField()
    restaurant_detail = serializers.SerializerMethodField()
    jalali_created_at = serializers.SerializerMethodField()
    jalali_updated_at = serializers.SerializerMethodField()
    jalali_cancellation_deadline = serializers.SerializerMethodField()
    
    available_quantity = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = DailyMenuMealOption
        fields = [
            'id', 'base_meal', 'base_meal_title', 'base_meal_image', 
            'restaurant_id', 'restaurant_name', 'restaurant_detail', 'title', 'description', 
            'price', 'quantity', 'reserved_quantity', 'available_quantity',
            'is_default', 'cancellation_deadline', 'jalali_cancellation_deadline',
            'created_at', 'jalali_created_at', 'updated_at', 'jalali_updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'reserved_quantity']
    
    def get_restaurant_name(self, obj):
        """نام رستوران از طریق base_meal یا daily_menu"""
        if obj.base_meal and obj.base_meal.restaurant:
            return obj.base_meal.restaurant.name
        if obj.daily_menu and obj.daily_menu.restaurant:
            return obj.daily_menu.restaurant.name
        return None
    
    def get_restaurant_id(self, obj):
        """ID رستوران از طریق base_meal یا daily_menu"""
        if obj.base_meal and obj.base_meal.restaurant:
            return obj.base_meal.restaurant.id
        if obj.daily_menu and obj.daily_menu.restaurant:
            return obj.daily_menu.restaurant.id
        return None
    
    def get_restaurant_detail(self, obj):
        """جزئیات رستوران از طریق base_meal یا daily_menu"""
        restaurant = None
        if obj.base_meal and obj.base_meal.restaurant:
            restaurant = obj.base_meal.restaurant
        elif obj.daily_menu and obj.daily_menu.restaurant:
            restaurant = obj.daily_menu.restaurant
        
        if restaurant:
            return RestaurantSerializer(restaurant).data
        return None
    
    @extend_schema_field(serializers.CharField())
    def get_base_meal_image(self, obj):
        """تصویر غذای پایه"""
        if obj.base_meal and obj.base_meal.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.base_meal.image.url)
            return obj.base_meal.image.url
        return None
    
    @extend_schema_field(serializers.CharField())
    def get_jalali_created_at(self, obj):
        if obj.created_at:
            return datetime2jalali(obj.created_at).strftime('%Y/%m/%d %H:%M')
        return None
    
    @extend_schema_field(serializers.CharField())
    def get_jalali_updated_at(self, obj):
        if obj.updated_at:
            return datetime2jalali(obj.updated_at).strftime('%Y/%m/%d %H:%M')
        return None
    
    @extend_schema_field(serializers.CharField())
    def get_jalali_cancellation_deadline(self, obj):
        """مهلت لغو (به صورت string)"""
        if obj.cancellation_deadline:
            return str(obj.cancellation_deadline)
        return None


class DailyMenuDessertOptionSerializer(serializers.ModelSerializer):
    """سریالایزر برای DailyMenuDessertOption"""
    base_dessert_title = serializers.CharField(source='base_dessert.title', read_only=True)
    base_dessert_image = serializers.SerializerMethodField()
    restaurant_name = serializers.SerializerMethodField()
    restaurant_id = serializers.SerializerMethodField()
    restaurant_detail = serializers.SerializerMethodField()
    jalali_created_at = serializers.SerializerMethodField()
    jalali_updated_at = serializers.SerializerMethodField()
    jalali_cancellation_deadline = serializers.SerializerMethodField()
    
    available_quantity = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = DailyMenuDessertOption
        fields = [
            'id', 'base_dessert', 'base_dessert_title', 'base_dessert_image', 
            'restaurant_id', 'restaurant_name', 'restaurant_detail', 'title', 'description', 
            'price', 'quantity', 'reserved_quantity', 'available_quantity',
            'is_default', 'cancellation_deadline', 'jalali_cancellation_deadline',
            'created_at', 'jalali_created_at', 'updated_at', 'jalali_updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'reserved_quantity']
    
    def get_restaurant_name(self, obj):
        """نام رستوران از طریق base_dessert یا daily_menu"""
        if obj.base_dessert and obj.base_dessert.restaurant:
            return obj.base_dessert.restaurant.name
        if obj.daily_menu and obj.daily_menu.restaurant:
            return obj.daily_menu.restaurant.name
        return None
    
    def get_restaurant_id(self, obj):
        """ID رستوران از طریق base_dessert یا daily_menu"""
        if obj.base_dessert and obj.base_dessert.restaurant:
            return obj.base_dessert.restaurant.id
        if obj.daily_menu and obj.daily_menu.restaurant:
            return obj.daily_menu.restaurant.id
        return None
    
    def get_restaurant_detail(self, obj):
        """جزئیات رستوران از طریق base_dessert یا daily_menu"""
        restaurant = None
        if obj.base_dessert and obj.base_dessert.restaurant:
            restaurant = obj.base_dessert.restaurant
        elif obj.daily_menu and obj.daily_menu.restaurant:
            restaurant = obj.daily_menu.restaurant
        
        if restaurant:
            return RestaurantSerializer(restaurant).data
        return None
    
    @extend_schema_field(serializers.CharField())
    def get_base_dessert_image(self, obj):
        """تصویر دسر پایه"""
        if obj.base_dessert and obj.base_dessert.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.base_dessert.image.url)
            return obj.base_dessert.image.url
        return None
    
    @extend_schema_field(serializers.CharField())
    def get_jalali_created_at(self, obj):
        if obj.created_at:
            return datetime2jalali(obj.created_at).strftime('%Y/%m/%d %H:%M')
        return None
    
    @extend_schema_field(serializers.CharField())
    def get_jalali_updated_at(self, obj):
        if obj.updated_at:
            return datetime2jalali(obj.updated_at).strftime('%Y/%m/%d %H:%M')
        return None
    
    @extend_schema_field(serializers.CharField())
    def get_jalali_cancellation_deadline(self, obj):
        """مهلت لغو (به صورت string)"""
        if obj.cancellation_deadline:
            return str(obj.cancellation_deadline)
        return None


class BaseMealWithOptionsSerializer(serializers.ModelSerializer):
    """BaseMeal با MealOption های مرتبط"""
    restaurant_name = serializers.CharField(source='restaurant.name', read_only=True)
    restaurant_id = serializers.IntegerField(source='restaurant.id', read_only=True)
    options = serializers.SerializerMethodField()
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = BaseMeal
        fields = [
            'id', 'title', 'description', 'ingredients', 'image', 'image_url',
            'restaurant', 'restaurant_id', 'restaurant_name',
            'is_active', 'options'
        ]
    
    def get_options(self, obj):
        """گزینه‌های غذا که در daily_menu موجود هستند"""
        # دریافت daily_menu از context
        daily_menu = self.context.get('daily_menu')
        if daily_menu:
            # فقط DailyMenuMealOption هایی که در daily_menu هستند
            options = daily_menu.menu_meal_options.filter(base_meal=obj).order_by('title')
            
            # استفاده از DailyMenuMealOptionSerializer
            return DailyMenuMealOptionSerializer(options, many=True, context=self.context).data
        return []
    
    def get_image_url(self, obj):
        """URL تصویر"""
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None


class DailyMenuSerializer(serializers.ModelSerializer):
    """سریالایزر منوی روزانه - ساختار ساده و استاندارد"""
    restaurant_name = serializers.CharField(source='restaurant.name', read_only=True)
    centers = serializers.SerializerMethodField()
    meals = serializers.SerializerMethodField()
    desserts = serializers.SerializerMethodField()
    jalali_date = serializers.SerializerMethodField()

    class Meta:
        model = DailyMenu
        fields = [
            'id', 'date', 'jalali_date', 'is_available', 'max_reservations_per_meal', 
            'restaurant_name', 'centers', 'meals', 'desserts'
        ]

    @extend_schema_field(serializers.ListField())
    def get_centers(self, obj):
        """لیست مراکز رستوران با logo"""
        if obj.restaurant:
            centers = obj.restaurant.centers.all()
            request = self.context.get('request')
            centers_data = []
            for center in centers:
                logo_url = None
                if center.logo:
                    if request:
                        logo_url = request.build_absolute_uri(center.logo.url)
                    else:
                        logo_url = center.logo.url
                
                centers_data.append({
                    'id': center.id,
                    'name': center.name,
                    'logo_url': logo_url
                })
            return centers_data
        return []

    @extend_schema_field(serializers.ListField())
    def get_meals(self, obj):
        """BaseMeal ها با MealOption های مرتبط - ساختار ساده و استاندارد"""
        base_meal_ids = obj.menu_meal_options.values_list('base_meal_id', flat=True).distinct()
        from apps.food_management.models import BaseMeal
        base_meals = BaseMeal.objects.filter(id__in=base_meal_ids).select_related('restaurant')
        
        request = self.context.get('request')
        meals_data = []
        for base_meal in base_meals:
            # دریافت options مرتبط با این base_meal
            options = obj.menu_meal_options.filter(base_meal=base_meal).order_by('title')
            
            # ساخت options ساده با available_quantity
            options_data = []
            for option in options:
                available_quantity = max(0, option.quantity - option.reserved_quantity)
                options_data.append({
                    'id': option.id,
                    'title': option.title,
                    'description': option.description or '',
                    'price': float(option.price),
                    'quantity': option.quantity,
                    'available_quantity': available_quantity
                })
            
            # دریافت URL تصویر غذای پایه
            image_url = None
            if base_meal.image:
                if request:
                    image_url = request.build_absolute_uri(base_meal.image.url)
                else:
                    image_url = base_meal.image.url
            
            meals_data.append({
                'id': base_meal.id,
                'title': base_meal.title,
                'description': base_meal.description or '',
                'ingredients': base_meal.ingredients or '',
                'image_url': image_url,
                'options': options_data
            })
        
        return meals_data

    @extend_schema_field(serializers.ListField())
    def get_desserts(self, obj):
        """BaseDessert ها با DessertOption های مرتبط - ساختار ساده و استاندارد"""
        base_dessert_ids = obj.menu_dessert_options.values_list('base_dessert_id', flat=True).distinct()
        from apps.food_management.models import BaseDessert
        base_desserts = BaseDessert.objects.filter(id__in=base_dessert_ids).select_related('restaurant')
        
        request = self.context.get('request')
        desserts_data = []
        for base_dessert in base_desserts:
            # دریافت options مرتبط با این base_dessert
            options = obj.menu_dessert_options.filter(base_dessert=base_dessert).order_by('title')
            
            # ساخت options ساده با available_quantity
            options_data = []
            for option in options:
                available_quantity = max(0, option.quantity - option.reserved_quantity)
                options_data.append({
                    'id': option.id,
                    'title': option.title,
                    'description': option.description or '',
                    'price': float(option.price),
                    'quantity': option.quantity,
                    'available_quantity': available_quantity
                })
            
            # دریافت URL تصویر دسر پایه
            image_url = None
            if base_dessert.image:
                if request:
                    image_url = request.build_absolute_uri(base_dessert.image.url)
                else:
                    image_url = base_dessert.image.url
            
            desserts_data.append({
                'id': base_dessert.id,
                'title': base_dessert.title,
                'description': base_dessert.description or '',
                'ingredients': base_dessert.ingredients or '',
                'image_url': image_url,
                'options': options_data
            })
        
        return desserts_data

    @extend_schema_field(serializers.CharField())
    def get_jalali_date(self, obj):
        if obj.date:
            return date2jalali(obj.date).strftime('%Y/%m/%d')
        return None


class SimpleBaseMealSerializer(serializers.ModelSerializer):
    """سریالایزر ساده برای غذای پایه"""
    image_url = serializers.SerializerMethodField()
    jalali_created_at = serializers.SerializerMethodField()
    jalali_updated_at = serializers.SerializerMethodField()
    
    class Meta:
        model = BaseMeal
        fields = [
            'id', 'title', 'description', 'ingredients', 'image', 'image_url', 
            'is_active', 'created_at', 'jalali_created_at', 
            'updated_at', 'jalali_updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_image_url(self, obj):
        """URL تصویر"""
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None

    @extend_schema_field(serializers.CharField())
    def get_jalali_created_at(self, obj):
        if obj.created_at:
            return datetime2jalali(obj.created_at).strftime('%Y/%m/%d %H:%M')
        return None

    @extend_schema_field(serializers.CharField())
    def get_jalali_updated_at(self, obj):
        if obj.updated_at:
            return datetime2jalali(obj.updated_at).strftime('%Y/%m/%d %H:%M')
        return None


# ========== Dessert Serializers ==========

class BaseDessertSerializer(serializers.ModelSerializer):
    """سریالایزر دسر پایه"""
    restaurant_name = serializers.CharField(source='restaurant.name', read_only=True)
    restaurant_detail = RestaurantSerializer(source='restaurant', read_only=True)
    jalali_created_at = serializers.SerializerMethodField()
    jalali_updated_at = serializers.SerializerMethodField()
    
    class Meta:
        model = BaseDessert
        fields = [
            'id', 'title', 'description', 'ingredients', 'image', 
            'restaurant', 'restaurant_name', 'restaurant_detail', 
            'is_active',
            'created_at', 'jalali_created_at', 'updated_at', 'jalali_updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # فیلتر کردن queryset رستوران‌ها - فقط رستوران‌های فعال
        if 'restaurant' in self.fields:
            self.fields['restaurant'].queryset = Restaurant.objects.filter(is_active=True)

    @extend_schema_field(serializers.CharField())
    def get_jalali_created_at(self, obj):
        if obj.created_at:
            return datetime2jalali(obj.created_at).strftime('%Y/%m/%d %H:%M')
        return None

    @extend_schema_field(serializers.CharField())
    def get_jalali_updated_at(self, obj):
        if obj.updated_at:
            return datetime2jalali(obj.updated_at).strftime('%Y/%m/%d %H:%M')
        return None
    
    def validate(self, data):
        """بررسی محدودیت رستوران"""
        restaurant = data.get('restaurant')
        
        # اگر از instance باشد (در زمان update)
        if not restaurant and self.instance:
            restaurant = self.instance.restaurant
        
        # رستوران باید انتخاب شود
        if not restaurant:
            raise serializers.ValidationError({
                'restaurant': 'رستوران باید انتخاب شود.'
            })
        
        return data


# برای سازگاری با کدهای قبلی
DessertSerializer = BaseDessertSerializer


class SimpleBaseDessertSerializer(serializers.ModelSerializer):
    """سریالایزر ساده برای دسر پایه"""
    image_url = serializers.SerializerMethodField()
    jalali_created_at = serializers.SerializerMethodField()
    jalali_updated_at = serializers.SerializerMethodField()
    
    class Meta:
        model = BaseDessert
        fields = [
            'id', 'title', 'description', 'ingredients', 'image', 'image_url', 
            'is_active', 'created_at', 'jalali_created_at', 
            'updated_at', 'jalali_updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_image_url(self, obj):
        """URL تصویر"""
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None

    @extend_schema_field(serializers.CharField())
    def get_jalali_created_at(self, obj):
        if obj.created_at:
            return datetime2jalali(obj.created_at).strftime('%Y/%m/%d %H:%M')
        return None

    @extend_schema_field(serializers.CharField())
    def get_jalali_updated_at(self, obj):
        if obj.updated_at:
            return datetime2jalali(obj.updated_at).strftime('%Y/%m/%d %H:%M')
        return None


# برای سازگاری با کدهای قبلی
SimpleDessertSerializer = SimpleBaseDessertSerializer




# برای سازگاری با کدهای قبلی
SimpleMealOptionSerializer = DailyMenuMealOptionSerializer
MealOptionInBaseMealSerializer = DailyMenuMealOptionSerializer
SimpleMealSerializer = SimpleMealOptionSerializer


class MealOptionUpdateSerializer(serializers.Serializer):
    """سریالایزر برای به‌روزرسانی اپشن غذا"""
    title = serializers.CharField(max_length=200)
    description = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    price = serializers.DecimalField(max_digits=10, decimal_places=2)
    quantity = serializers.IntegerField(min_value=0)
    cancellation_deadline = serializers.CharField(required=False, allow_null=True, allow_blank=True)


class DailyMenuMealUpdateSerializer(serializers.Serializer):
    """سریالایزر برای افزودن/ویرایش یک غذا در منوی روزانه"""
    restaurant_id = serializers.IntegerField()
    base_meal_id = serializers.IntegerField()
    meal_options = MealOptionUpdateSerializer(many=True)


class SimpleEmployeeRestaurantSerializer(serializers.ModelSerializer):
    """سریالایزر ساده رستوران برای کارمند"""
    center = serializers.SerializerMethodField()
    
    class Meta:
        model = Restaurant
        fields = ['id', 'name', 'center']
    
    @extend_schema_field(CenterSerializer())
    def get_center(self, obj):
        """اولین مرکز را برمی‌گرداند"""
        if obj.centers.exists():
            return CenterSerializer(obj.centers.first()).data
        return None


class SimpleEmployeeDailyMenuSerializer(serializers.ModelSerializer):
    """سریالایزر ساده منوی روزانه برای کارمند"""
    restaurant = SimpleEmployeeRestaurantSerializer(read_only=True)
    jalali_date = serializers.SerializerMethodField()
    meals = serializers.SerializerMethodField()
    desserts = serializers.SerializerMethodField()
    
    class Meta:
        model = DailyMenu
        fields = [
            'id', 'date', 'jalali_date', 'is_available', 
            'restaurant', 'meals', 'desserts'
        ]
    
    @extend_schema_field(serializers.CharField())
    def get_jalali_date(self, obj):
        if obj.date:
            return date2jalali(obj.date).strftime('%Y/%m/%d')
        return None
    
    @extend_schema_field(serializers.ListField())
    def get_meals(self, obj):
        """لیست غذاها با اپشن‌هایشان - ساختار ساده"""
        base_meal_ids = obj.menu_meal_options.values_list('base_meal_id', flat=True).distinct()
        from apps.food_management.models import BaseMeal
        base_meals = BaseMeal.objects.filter(id__in=base_meal_ids)
        
        request = self.context.get('request')
        meals_data = []
        for base_meal in base_meals:
            # دریافت options مرتبط با این base_meal
            options = obj.menu_meal_options.filter(base_meal=base_meal).order_by('title')
            
            # ساخت options ساده
            options_data = []
            for option in options:
                options_data.append({
                    'id': option.id,
                    'title': option.title,
                    'price': float(option.price),
                    'quantity': option.quantity,
                    'available_quantity': max(0, option.quantity - option.reserved_quantity)
                })
            
            # دریافت URL تصویر غذای پایه
            image_url = None
            if base_meal.image:
                if request:
                    image_url = request.build_absolute_uri(base_meal.image.url)
                else:
                    image_url = base_meal.image.url
            
            meals_data.append({
                'id': base_meal.id,
                'title': base_meal.title,
                'ingredients': base_meal.ingredients or '',
                'image': image_url,
                'options': options_data
            })
        
        return meals_data
    
    @extend_schema_field(serializers.ListField())
    def get_desserts(self, obj):
        """لیست دسرها با اپشن‌هایشان - ساختار ساده"""
        base_dessert_ids = obj.menu_dessert_options.values_list('base_dessert_id', flat=True).distinct()
        from apps.food_management.models import BaseDessert
        base_desserts = BaseDessert.objects.filter(id__in=base_dessert_ids)
        
        request = self.context.get('request')
        desserts_data = []
        for base_dessert in base_desserts:
            # دریافت options مرتبط با این base_dessert
            options = obj.menu_dessert_options.filter(base_dessert=base_dessert).order_by('title')
            
            # ساخت options ساده
            options_data = []
            for option in options:
                options_data.append({
                    'id': option.id,
                    'title': option.title,
                    'price': float(option.price),
                    'quantity': option.quantity,
                    'available_quantity': max(0, option.quantity - option.reserved_quantity)
                })
            
            # دریافت URL تصویر دسر پایه
            image_url = None
            if base_dessert.image:
                if request:
                    image_url = request.build_absolute_uri(base_dessert.image.url)
                else:
                    image_url = base_dessert.image.url
            
            desserts_data.append({
                'id': base_dessert.id,
                'title': base_dessert.title,
                'ingredients': base_dessert.ingredients or '',
                'image': image_url,
                'options': options_data
            })
        
        return desserts_data

