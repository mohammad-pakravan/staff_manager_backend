from rest_framework import serializers
from django.utils import timezone
from drf_spectacular.utils import extend_schema_field
from datetime import datetime
import jdatetime
from .models import (
    Restaurant, BaseMeal, MealOption, DailyMenu, 
    FoodReservation, FoodReport, GuestReservation
)
# برای سازگاری با کدهای قبلی
Meal = BaseMeal


class RestaurantSerializer(serializers.ModelSerializer):
    """سریالایزر رستوران"""
    center_id = serializers.IntegerField(source='center.id', read_only=True)
    center_name = serializers.CharField(source='center.name', read_only=True)
    jalali_created_at = serializers.SerializerMethodField()
    jalali_updated_at = serializers.SerializerMethodField()
    
    class Meta:
        model = Restaurant
        fields = [
            'id', 'name', 'center_name', 'center_id', 'address', 'phone', 'email', 
            'description', 'is_active', 'created_at', 'jalali_created_at', 
            'updated_at', 'jalali_updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

    @extend_schema_field(serializers.CharField())
    def get_jalali_created_at(self, obj):
        if obj.created_at:
            return jdatetime.datetime.fromgregorian(datetime=obj.created_at).strftime('%Y/%m/%d %H:%M')
        return None

    @extend_schema_field(serializers.CharField())
    def get_jalali_updated_at(self, obj):
        if obj.updated_at:
            return jdatetime.datetime.fromgregorian(datetime=obj.updated_at).strftime('%Y/%m/%d %H:%M')
        return None


class BaseMealSerializer(serializers.ModelSerializer):
    """سریالایزر غذای پایه"""
    center_name = serializers.CharField(source='center.name', read_only=True)
    restaurant_name = serializers.CharField(source='restaurant.name', read_only=True)
    restaurant_detail = RestaurantSerializer(source='restaurant', read_only=True)
    options = serializers.SerializerMethodField()
    jalali_created_at = serializers.SerializerMethodField()
    jalali_updated_at = serializers.SerializerMethodField()
    jalali_cancellation_deadline = serializers.SerializerMethodField()
    
    class Meta:
        model = BaseMeal
        fields = [
            'id', 'title', 'description', 'image', 
            'center', 'center_name', 'restaurant', 'restaurant_name', 'restaurant_detail', 
            'cancellation_deadline', 'jalali_cancellation_deadline',
            'is_active', 'options',
            'created_at', 'jalali_created_at', 'updated_at', 'jalali_updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # فیلتر کردن queryset رستوران‌ها بر اساس مرکز
        if 'restaurant' in self.fields:
            # چک کردن اینکه instance یک object است نه QuerySet
            if self.instance and not hasattr(self.instance, '__iter__') and hasattr(self.instance, 'center'):
                if self.instance.center:
                    self.fields['restaurant'].queryset = Restaurant.objects.filter(
                        center=self.instance.center,
                        is_active=True
                    )
            elif hasattr(self, 'initial_data'):
                center_id = self.initial_data.get('center')
                if center_id:
                    try:
                        from apps.centers.models import Center
                        center = Center.objects.get(pk=center_id)
                        self.fields['restaurant'].queryset = Restaurant.objects.filter(
                            center=center,
                            is_active=True
                        )
                    except (Center.DoesNotExist, ValueError, TypeError):
                        pass

    @extend_schema_field(serializers.ListField())
    def get_options(self, obj):
        """گزینه‌های غذا"""
        options = obj.options.filter(is_active=True).order_by('sort_order', 'title')
        return MealOptionSerializer(options, many=True).data

    @extend_schema_field(serializers.CharField())
    def get_jalali_created_at(self, obj):
        if obj.created_at:
            return jdatetime.datetime.fromgregorian(datetime=obj.created_at).strftime('%Y/%m/%d %H:%M')
        return None

    @extend_schema_field(serializers.CharField())
    def get_jalali_updated_at(self, obj):
        if obj.updated_at:
            return jdatetime.datetime.fromgregorian(datetime=obj.updated_at).strftime('%Y/%m/%d %H:%M')
        return None
    
    @extend_schema_field(serializers.CharField())
    def get_jalali_cancellation_deadline(self, obj):
        """مهلت لغو به شمسی"""
        if obj.cancellation_deadline:
            return jdatetime.datetime.fromgregorian(datetime=obj.cancellation_deadline).strftime('%Y/%m/%d %H:%M')
        return None
    
    def validate(self, data):
        """بررسی محدودیت مرکز"""
        restaurant = data.get('restaurant')
        center = data.get('center')
        
        # اگر از instance باشد (در زمان update)
        if not restaurant and self.instance:
            restaurant = self.instance.restaurant
        if not center and self.instance:
            center = self.instance.center
        
        if restaurant and center:
            if restaurant.center != center:
                raise serializers.ValidationError({
                    'restaurant': f'رستوران باید متعلق به مرکز "{center.name}" باشد. رستوران انتخاب شده متعلق به مرکز "{restaurant.center.name}" است.'
                })
        
        return data


class MealOptionSerializer(serializers.ModelSerializer):
    """سریالایزر غذای اصلی"""
    base_meal_title = serializers.CharField(source='base_meal.title', read_only=True)
    base_meal_image = serializers.SerializerMethodField()
    restaurant_name = serializers.CharField(source='restaurant.name', read_only=True)
    restaurant_id = serializers.IntegerField(source='restaurant.id', read_only=True)
    restaurant_detail = serializers.SerializerMethodField()
    jalali_created_at = serializers.SerializerMethodField()
    jalali_updated_at = serializers.SerializerMethodField()
    
    available_quantity = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = MealOption
        fields = [
            'id', 'base_meal', 'base_meal_title', 'base_meal_image', 
            'restaurant_id', 'restaurant_name', 'restaurant_detail', 'title', 'description', 
            'price', 'quantity', 'reserved_quantity', 'available_quantity',
            'is_active', 'is_default', 'sort_order',
            'created_at', 'jalali_created_at', 'updated_at', 'jalali_updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'reserved_quantity']
    
    def get_restaurant_detail(self, obj):
        """جزئیات رستوران از طریق base_meal"""
        if obj.restaurant:
            return RestaurantSerializer(obj.restaurant).data
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
            return jdatetime.datetime.fromgregorian(datetime=obj.created_at).strftime('%Y/%m/%d %H:%M')
        return None

    @extend_schema_field(serializers.CharField())
    def get_jalali_updated_at(self, obj):
        if obj.updated_at:
            return jdatetime.datetime.fromgregorian(datetime=obj.updated_at).strftime('%Y/%m/%d %H:%M')
        return None


# برای سازگاری با کدهای قبلی
MealSerializer = BaseMealSerializer


 

class BaseMealWithOptionsSerializer(serializers.ModelSerializer):
    """BaseMeal با MealOption های مرتبط"""
    center_name = serializers.CharField(source='center.name', read_only=True)
    restaurant_name = serializers.CharField(source='restaurant.name', read_only=True)
    restaurant_id = serializers.IntegerField(source='restaurant.id', read_only=True)
    options = serializers.SerializerMethodField()
    image_url = serializers.SerializerMethodField()
    jalali_cancellation_deadline = serializers.SerializerMethodField()

    class Meta:
        model = BaseMeal
        fields = [
            'id', 'title', 'description', 'image', 'image_url',
            'center', 'center_name', 'restaurant', 'restaurant_id', 'restaurant_name',
            'cancellation_deadline', 'jalali_cancellation_deadline',
            'is_active', 'options'
        ]
    
    def get_options(self, obj):
        """گزینه‌های غذا که در daily_menu موجود هستند"""
        # دریافت daily_menu از context
        daily_menu = self.context.get('daily_menu')
        if daily_menu:
            # فقط MealOption هایی که در daily_menu هستند
            options = obj.options.filter(
                id__in=daily_menu.meal_options.values_list('id', flat=True),
                is_active=True
            ).order_by('sort_order', 'title')
            
            # استفاده از MealOptionInBaseMealSerializer که اطلاعات تکراری BaseMeal را ندارد
            return MealOptionInBaseMealSerializer(options, many=True, context=self.context).data
        return []
    
    def get_image_url(self, obj):
        """URL تصویر"""
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None

    @extend_schema_field(serializers.CharField())
    def get_jalali_cancellation_deadline(self, obj):
        """مهلت لغو به شمسی"""
        if obj.cancellation_deadline:
            return jdatetime.datetime.fromgregorian(datetime=obj.cancellation_deadline).strftime('%Y/%m/%d %H:%M')
        return None


class DailyMenuSerializer(serializers.ModelSerializer):
    meals = serializers.SerializerMethodField()  # BaseMeal ها با options
    meal_options = serializers.SerializerMethodField()  # برای سازگاری با کدهای قبلی (لیست تخت)
    base_meals = serializers.SerializerMethodField()  # برای سازگاری با کدهای قبلی
    center_name = serializers.CharField(source='center.name', read_only=True)
    meals_count = serializers.SerializerMethodField()
    jalali_date = serializers.SerializerMethodField()

    class Meta:
        model = DailyMenu
        fields = [
            'id', 'center', 'date', 'jalali_date', 'meals', 'meal_options', 'base_meals', 'meals_count',
            'max_reservations_per_meal', 'is_available', 'center_name'
        ]

    @extend_schema_field(BaseMealWithOptionsSerializer(many=True))
    def get_meals(self, obj):
        """BaseMeal ها با MealOption های مرتبط"""
        base_meal_ids = obj.meal_options.values_list('base_meal_id', flat=True).distinct()
        from .models import BaseMeal
        base_meals = BaseMeal.objects.filter(id__in=base_meal_ids).select_related('center', 'restaurant')
        
        # اضافه کردن daily_menu به context
        context = self.context.copy()
        context['daily_menu'] = obj
        
        return BaseMealWithOptionsSerializer(base_meals, many=True, context=context).data

    @extend_schema_field(MealOptionSerializer(many=True))
    def get_meal_options(self, obj):
        """برای سازگاری با کدهای قبلی - لیست تخت MealOption ها"""
        options = obj.meal_options.filter(is_active=True).order_by('sort_order', 'title')
        return MealOptionSerializer(options, many=True, context=self.context).data

    @extend_schema_field(BaseMealSerializer(many=True))
    def get_base_meals(self, obj):
        """برای سازگاری با کدهای قبلی"""
        base_meal_ids = obj.meal_options.values_list('base_meal_id', flat=True).distinct()
        from .models import BaseMeal
        base_meals = BaseMeal.objects.filter(id__in=base_meal_ids)
        return BaseMealSerializer(base_meals, many=True).data

    @extend_schema_field(serializers.IntegerField())
    def get_meals_count(self, obj):
        return obj.meal_options.count()

    @extend_schema_field(serializers.CharField())
    def get_jalali_date(self, obj):
        if obj.date:
            return jdatetime.date.fromgregorian(date=obj.date).strftime('%Y/%m/%d')
        return None


class FoodReservationSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.username', read_only=True)
    user_full_name = serializers.SerializerMethodField()
    meal = MealSerializer(read_only=True)
    daily_menu = DailyMenuSerializer(read_only=True)
    can_cancel = serializers.SerializerMethodField()
    time_until_cancellation = serializers.SerializerMethodField()
    jalali_reservation_date = serializers.SerializerMethodField()
    jalali_cancellation_deadline = serializers.SerializerMethodField()
    jalali_cancelled_at = serializers.SerializerMethodField()

    class Meta:
        model = FoodReservation
        fields = [
            'id', 'user', 'user_name', 'user_full_name', 'daily_menu', 'meal', 'quantity', 'amount',
            'reservation_date', 'jalali_reservation_date', 'status', 'cancellation_deadline', 
            'jalali_cancellation_deadline', 'cancelled_at', 'jalali_cancelled_at',
            'can_cancel', 'time_until_cancellation'
        ]
        read_only_fields = [
            'reservation_date', 'cancellation_deadline', 'cancelled_at'
        ]

    @extend_schema_field(serializers.CharField())
    def get_user_full_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}".strip()

    @extend_schema_field(serializers.BooleanField())
    def get_can_cancel(self, obj):
        return obj.can_cancel()

    @extend_schema_field(serializers.CharField())
    def get_time_until_cancellation(self, obj):
        if obj.status == 'reserved':
            now = timezone.now()
            if obj.cancellation_deadline and now < obj.cancellation_deadline:
                delta = obj.cancellation_deadline - now
                hours = delta.total_seconds() // 3600
                minutes = (delta.total_seconds() % 3600) // 60
                return f"{int(hours)} ساعت و {int(minutes)} دقیقه"
            return "مهلت لغو گذشته"
        return None

    @extend_schema_field(serializers.CharField())
    def get_jalali_reservation_date(self, obj):
        if obj.reservation_date:
            return jdatetime.datetime.fromgregorian(datetime=obj.reservation_date).strftime('%Y/%m/%d %H:%M')
        return None

    @extend_schema_field(serializers.CharField())
    def get_jalali_cancellation_deadline(self, obj):
        if obj.cancellation_deadline:
            return jdatetime.datetime.fromgregorian(datetime=obj.cancellation_deadline).strftime('%Y/%m/%d %H:%M')
        return None

    @extend_schema_field(serializers.CharField())
    def get_jalali_cancelled_at(self, obj):
        if obj.cancelled_at:
            return jdatetime.datetime.fromgregorian(datetime=obj.cancelled_at).strftime('%Y/%m/%d %H:%M')
        return None


class FoodReservationCreateSerializer(serializers.ModelSerializer):
    meal = serializers.PrimaryKeyRelatedField(read_only=True, required=False, allow_null=True)  # برای سازگاری
    
    class Meta:
        model = FoodReservation
        fields = ['daily_menu', 'meal_option', 'meal', 'quantity']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # افزودن فیلد base_meal برای validation (نه در Meta.fields)
        self.fields['base_meal'] = serializers.PrimaryKeyRelatedField(
            queryset=BaseMeal.objects.all(),
            required=True,
            write_only=True,
            help_text='ID غذای پایه'
        )
        # Set queryset for meal_option
        if self.context.get('request'):
            self.fields['meal_option'] = serializers.PrimaryKeyRelatedField(
                queryset=MealOption.objects.filter(is_active=True),
                required=True
            )

    def validate(self, data):
        user = self.context['request'].user
        daily_menu = data.get('daily_menu')
        base_meal = data.get('base_meal')
        meal_option = data.get('meal_option')
        quantity = data.get('quantity', 1)
        
        if not base_meal:
            raise serializers.ValidationError({"base_meal": "غذای پایه الزامی است."})
        
        if not meal_option:
            raise serializers.ValidationError({"meal_option": "گزینه غذا الزامی است."})
        
        # بررسی اینکه meal_option متعلق به base_meal است
        if meal_option.base_meal != base_meal:
            raise serializers.ValidationError({
                "meal_option": f"گزینه غذا '{meal_option.title}' متعلق به غذای پایه '{base_meal.title}' نیست."
            })
        
        # بررسی اینکه غذا در منوی روزانه موجود است
        if not daily_menu.meal_options.filter(id=meal_option.id).exists():
            raise serializers.ValidationError({
                "meal_option": "این غذا در منوی روزانه موجود نیست."
            })
        
        # بررسی تعداد موجود در meal_option
        # استفاده از reserved_quantity که خودکار به‌روزرسانی می‌شود
        meal_option.refresh_from_db()  # اطمینان از آخرین مقدار
        
        # محاسبه تعداد رزرو شده برای این meal_option در daily_menu (فقط برای این daily_menu)
        from django.db.models import Sum
        reserved_quantity_in_menu = FoodReservation.objects.filter(
            daily_menu=daily_menu,
            meal_option=meal_option,
            status='reserved'
        ).aggregate(total=Sum('quantity'))['total'] or 0
        
        # تعداد رزروهای مهمان در این daily_menu
        reserved_guest_in_menu = GuestReservation.objects.filter(
            daily_menu=daily_menu,
            meal_option=meal_option,
            status='reserved'
        ).count()
        
        # اگر در حال اپدیت هستیم، رزرو فعلی را از محاسبه کم می‌کنیم
        if self.instance:
            if self.instance.status == 'reserved':
                if self.instance.__class__ == FoodReservation:
                    reserved_quantity_in_menu = max(0, reserved_quantity_in_menu - self.instance.quantity)
                elif self.instance.__class__ == GuestReservation:
                    reserved_guest_in_menu = max(0, reserved_guest_in_menu - 1)
        
        total_reserved_in_menu = reserved_quantity_in_menu + reserved_guest_in_menu
        
        # بررسی اینکه آیا تعداد کافی موجود است
        available_quantity = meal_option.quantity - total_reserved_in_menu
        
        if quantity > available_quantity:
            raise serializers.ValidationError(
                f"تعداد موجود برای '{meal_option.title}' کافی نیست. "
                f"در حال حاضر {available_quantity} عدد موجود است و شما می‌خواهید {quantity} عدد رزرو کنید."
            )
        
        # محدودیت رزرو برای کاربران برداشته شده است
        # کاربران می‌توانند نامحدود رزرو کنند
        
        return data
    
    def create(self, validated_data):
        """ایجاد رزرو - حذف base_meal از validated_data"""
        # حذف base_meal چون در مدل وجود ندارد (فقط برای validation استفاده می‌شود)
        base_meal = validated_data.pop('base_meal', None)
        # اطمینان از حذف کامل
        if 'base_meal' in validated_data:
            del validated_data['base_meal']
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        """به‌روزرسانی رزرو - حذف base_meal از validated_data"""
        # حذف base_meal چون در مدل وجود ندارد (فقط برای validation استفاده می‌شود)
        validated_data.pop('base_meal', None)
        return super().update(instance, validated_data)


class SimpleMealOptionSerializer(serializers.ModelSerializer):
    """سریالایزر ساده برای غذای اصلی - با اطلاعات BaseMeal"""
    base_meal_title = serializers.CharField(source='base_meal.title', read_only=True)
    base_meal_image = serializers.SerializerMethodField()
    restaurant_name = serializers.CharField(source='restaurant.name', read_only=True)
    restaurant_id = serializers.IntegerField(source='restaurant.id', read_only=True)
    
    available_quantity = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = MealOption
        fields = [
            'id', 'base_meal', 'base_meal_title', 'base_meal_image', 
            'restaurant_id', 'restaurant_name', 'title', 'description', 'price', 
            'quantity', 'reserved_quantity', 'available_quantity'
        ]

    @extend_schema_field(serializers.CharField())
    def get_base_meal_image(self, obj):
        """تصویر غذای پایه"""
        if obj.base_meal and obj.base_meal.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.base_meal.image.url)
            return obj.base_meal.image.url
        return None


class MealOptionInBaseMealSerializer(serializers.ModelSerializer):
    """سریالایزر MealOption برای استفاده در BaseMeal - بدون اطلاعات تکراری"""
    available_quantity = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = MealOption
        fields = [
            'id', 'title', 'description', 'price', 
            'quantity', 'reserved_quantity', 'available_quantity',
            'is_active', 'is_default', 'sort_order'
        ]
        read_only_fields = ['reserved_quantity']


class SimpleBaseMealSerializer(serializers.ModelSerializer):
    """سریالایزر ساده برای غذای پایه"""
    class Meta:
        model = BaseMeal
        fields = ['id', 'title', 'description', 'image']


# برای سازگاری با کدهای قبلی
SimpleMealSerializer = SimpleMealOptionSerializer


class SimpleFoodReservationSerializer(serializers.ModelSerializer):
    """سریالایزر ساده برای رزرو غذا - فقط اطلاعات ضروری"""
    meal = serializers.SerializerMethodField()  # BaseMeal با meal_option داخلش
    jalali_reservation_date = serializers.SerializerMethodField()
    
    class Meta:
        model = FoodReservation
        fields = [
            'id', 'meal', 'quantity', 'status', 
            'reservation_date', 'jalali_reservation_date'
        ]
        read_only_fields = ['reservation_date']

    @extend_schema_field(BaseMealWithOptionsSerializer())
    def get_meal(self, obj):
        """BaseMeal با meal_option مربوطه داخلش"""
        if obj.meal_option and obj.meal_option.base_meal:
            base_meal = obj.meal_option.base_meal
            
            # ساخت context با daily_menu برای BaseMealWithOptionsSerializer
            context = self.context.copy()
            if obj.daily_menu:
                context['daily_menu'] = obj.daily_menu
            
            # استفاده از BaseMealWithOptionsSerializer
            serializer = BaseMealWithOptionsSerializer(base_meal, context=context)
            data = serializer.data
            
            # فقط meal_option مربوطه را در options نگه داریم
            if 'options' in data:
                meal_option_data = SimpleMealOptionSerializer(obj.meal_option, context=self.context).data
                data['options'] = [meal_option_data]
            
            return data
        return None

    @extend_schema_field(serializers.CharField())
    def get_jalali_reservation_date(self, obj):
        if obj.reservation_date:
            return jdatetime.datetime.fromgregorian(datetime=obj.reservation_date).strftime('%Y/%m/%d %H:%M')
        return None


class SimpleGuestReservationSerializer(serializers.ModelSerializer):
    """سریالایزر ساده برای رزرو مهمان - فقط اطلاعات ضروری"""
    meal = serializers.SerializerMethodField()  # BaseMeal با meal_option داخلش
    guest_full_name = serializers.SerializerMethodField()
    jalali_reservation_date = serializers.SerializerMethodField()
    
    class Meta:
        model = GuestReservation
        fields = [
            'id', 'guest_first_name', 'guest_last_name', 'guest_full_name',
            'meal', 'status', 'reservation_date', 'jalali_reservation_date'
        ]
        read_only_fields = ['reservation_date']

    @extend_schema_field(serializers.CharField())
    def get_guest_full_name(self, obj):
        return f"{obj.guest_first_name} {obj.guest_last_name}".strip()

    @extend_schema_field(BaseMealWithOptionsSerializer())
    def get_meal(self, obj):
        """BaseMeal با meal_option مربوطه داخلش"""
        if obj.meal_option and obj.meal_option.base_meal:
            base_meal = obj.meal_option.base_meal
            
            # ساخت context با daily_menu برای BaseMealWithOptionsSerializer
            context = self.context.copy()
            if obj.daily_menu:
                context['daily_menu'] = obj.daily_menu
            
            # استفاده از BaseMealWithOptionsSerializer
            serializer = BaseMealWithOptionsSerializer(base_meal, context=context)
            data = serializer.data
            
            # فقط meal_option مربوطه را در options نگه داریم
            if 'options' in data:
                meal_option_data = SimpleMealOptionSerializer(obj.meal_option, context=self.context).data
                data['options'] = [meal_option_data]
            
            return data
        return None

    @extend_schema_field(serializers.CharField())
    def get_jalali_reservation_date(self, obj):
        if obj.reservation_date:
            return jdatetime.datetime.fromgregorian(datetime=obj.reservation_date).strftime('%Y/%m/%d %H:%M')
        return None


class FoodReportSerializer(serializers.ModelSerializer):
    center_name = serializers.CharField(source='center.name', read_only=True)

    class Meta:
        model = FoodReport
        fields = [
            'id', 'center', 'center_name', 'report_date',
            'total_reservations', 'total_served', 'total_cancelled',
            'created_at'
        ]
        read_only_fields = ['created_at']




class MealStatisticsSerializer(serializers.Serializer):
    """سریالایزر آمار غذا"""
    total_meals = serializers.IntegerField()
    active_meals = serializers.IntegerField()
    total_reservations = serializers.IntegerField()
    today_reservations = serializers.IntegerField()
    cancelled_reservations = serializers.IntegerField()
    served_reservations = serializers.IntegerField()


class GuestReservationSerializer(serializers.ModelSerializer):
    """Serializer for GuestReservation model"""
    host_user_name = serializers.CharField(source='host_user.username', read_only=True)
    host_user_full_name = serializers.SerializerMethodField()
    guest_full_name = serializers.SerializerMethodField()
    meal = MealSerializer(read_only=True)
    daily_menu = DailyMenuSerializer(read_only=True)
    can_cancel = serializers.SerializerMethodField()
    time_until_cancellation = serializers.SerializerMethodField()
    jalali_reservation_date = serializers.SerializerMethodField()
    jalali_cancellation_deadline = serializers.SerializerMethodField()
    jalali_cancelled_at = serializers.SerializerMethodField()

    class Meta:
        model = GuestReservation
        fields = [
            'id', 'host_user', 'host_user_name', 'host_user_full_name',
            'guest_first_name', 'guest_last_name', 'guest_full_name',
            'daily_menu', 'meal', 'amount', 'reservation_date', 'jalali_reservation_date', 
            'status', 'cancellation_deadline', 'jalali_cancellation_deadline', 
            'cancelled_at', 'jalali_cancelled_at', 'can_cancel', 'time_until_cancellation'
        ]
        read_only_fields = [
            'reservation_date', 'cancellation_deadline', 'cancelled_at'
        ]

    @extend_schema_field(serializers.CharField())
    def get_host_user_full_name(self, obj):
        return f"{obj.host_user.first_name} {obj.host_user.last_name}".strip()

    @extend_schema_field(serializers.CharField())
    def get_guest_full_name(self, obj):
        return f"{obj.guest_first_name} {obj.guest_last_name}".strip()

    @extend_schema_field(serializers.BooleanField())
    def get_can_cancel(self, obj):
        return obj.can_cancel()

    @extend_schema_field(serializers.CharField())
    def get_time_until_cancellation(self, obj):
        if obj.status == 'reserved':
            now = timezone.now()
            if obj.cancellation_deadline and now < obj.cancellation_deadline:
                delta = obj.cancellation_deadline - now
                hours = delta.total_seconds() // 3600
                minutes = (delta.total_seconds() % 3600) // 60
                return f"{int(hours)} ساعت و {int(minutes)} دقیقه"
            return "مهلت لغو گذشته"
        return None

    @extend_schema_field(serializers.CharField())
    def get_jalali_reservation_date(self, obj):
        if obj.reservation_date:
            return jdatetime.datetime.fromgregorian(datetime=obj.reservation_date).strftime('%Y/%m/%d %H:%M')
        return None

    @extend_schema_field(serializers.CharField())
    def get_jalali_cancellation_deadline(self, obj):
        if obj.cancellation_deadline:
            return jdatetime.datetime.fromgregorian(datetime=obj.cancellation_deadline).strftime('%Y/%m/%d %H:%M')
        return None

    @extend_schema_field(serializers.CharField())
    def get_jalali_cancelled_at(self, obj):
        if obj.cancelled_at:
            return jdatetime.datetime.fromgregorian(datetime=obj.cancelled_at).strftime('%Y/%m/%d %H:%M')
        return None


class GuestReservationCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating GuestReservation"""
    meal = serializers.PrimaryKeyRelatedField(read_only=True, required=False, allow_null=True)  # برای سازگاری
    
    class Meta:
        model = GuestReservation
        fields = ['guest_first_name', 'guest_last_name', 'daily_menu', 'meal_option', 'meal']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # افزودن فیلد base_meal برای validation (نه در Meta.fields)
        self.fields['base_meal'] = serializers.PrimaryKeyRelatedField(
            queryset=BaseMeal.objects.all(),
            required=True,
            write_only=True,
            help_text='ID غذای پایه'
        )
        # Set queryset for meal_option
        if self.context.get('request'):
            self.fields['meal_option'] = serializers.PrimaryKeyRelatedField(
                queryset=MealOption.objects.filter(is_active=True),
                required=True
            )

    def validate(self, data):
        user = self.context['request'].user
        daily_menu = data.get('daily_menu')
        base_meal = data.get('base_meal')
        meal_option = data.get('meal_option')
        
        if not base_meal:
            raise serializers.ValidationError({"base_meal": "غذای پایه الزامی است."})
        
        if not meal_option:
            raise serializers.ValidationError({"meal_option": "گزینه غذا الزامی است."})
        
        # بررسی اینکه meal_option متعلق به base_meal است
        if meal_option.base_meal != base_meal:
            raise serializers.ValidationError({
                "meal_option": f"گزینه غذا '{meal_option.title}' متعلق به غذای پایه '{base_meal.title}' نیست."
            })
        
        # بررسی اینکه غذا در منوی روزانه موجود است
        if not daily_menu.meal_options.filter(id=meal_option.id).exists():
            raise serializers.ValidationError({
                "meal_option": "این غذا در منوی روزانه موجود نیست."
            })
        
        # بررسی تعداد موجود در meal_option (رزرو مهمان = 1 واحد)
        meal_option.refresh_from_db()  # اطمینان از آخرین مقدار
        
        # محاسبه تعداد رزرو شده برای این meal_option در daily_menu
        from django.db.models import Sum
        
        # تعداد رزروهای عادی (با quantity)
        reserved_quantity_normal = FoodReservation.objects.filter(
            daily_menu=daily_menu,
            meal_option=meal_option,
            status='reserved'
        ).aggregate(total=Sum('quantity'))['total'] or 0
        
        # تعداد رزروهای مهمان (هر رزرو = 1 واحد)
        reserved_quantity_guest = GuestReservation.objects.filter(
            daily_menu=daily_menu,
            meal_option=meal_option,
            status='reserved'
        ).count()
        
        # اگر در حال اپدیت هستیم، رزرو فعلی مهمان را از محاسبه کم می‌کنیم
        if self.instance:
            if self.instance.status == 'reserved':
                reserved_quantity_guest = max(0, reserved_quantity_guest - 1)
        
        total_reserved = reserved_quantity_normal + reserved_quantity_guest
        
        # بررسی اینکه آیا تعداد کافی موجود است (رزرو مهمان = 1 واحد)
        available_quantity = meal_option.quantity - total_reserved
        
        if available_quantity < 1:
            raise serializers.ValidationError(
                f"تعداد موجود برای '{meal_option.title}' کافی نیست. "
                f"در حال حاضر {available_quantity} عدد موجود است و برای رزرو مهمان حداقل 1 عدد نیاز است."
            )
        
        # محدودیت رزرو برای کاربران برداشته شده است
        # کاربران می‌توانند نامحدود رزرو کنند
        
        return data
    
    def create(self, validated_data):
        """ایجاد رزرو مهمان - حذف base_meal از validated_data"""
        # حذف base_meal چون در مدل وجود ندارد (فقط برای validation استفاده می‌شود)
        base_meal = validated_data.pop('base_meal', None)
        # اطمینان از حذف کامل
        if 'base_meal' in validated_data:
            del validated_data['base_meal']
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        """به‌روزرسانی رزرو مهمان - حذف base_meal از validated_data"""
        # حذف base_meal چون در مدل وجود ندارد (فقط برای validation استفاده می‌شود)
        validated_data.pop('base_meal', None)
        return super().update(instance, validated_data)


# ========== Report Serializers ==========

class MealOptionReportSerializer(serializers.Serializer):
    """سریالایزر گزارش بر اساس MealOption"""
    meal_option_id = serializers.IntegerField()
    meal_option_title = serializers.CharField()
    base_meal_title = serializers.CharField()
    restaurant_name = serializers.CharField()
    restaurant_id = serializers.IntegerField()
    center_name = serializers.CharField()
    center_id = serializers.IntegerField()
    total_reservations = serializers.IntegerField()
    reserved_count = serializers.IntegerField()
    cancelled_count = serializers.IntegerField()
    served_count = serializers.IntegerField()
    total_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    reserved_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    served_amount = serializers.DecimalField(max_digits=10, decimal_places=2)


class BaseMealReportSerializer(serializers.Serializer):
    """سریالایزر گزارش بر اساس BaseMeal"""
    base_meal_id = serializers.IntegerField()
    base_meal_title = serializers.CharField()
    restaurant_name = serializers.CharField()
    center_name = serializers.CharField()
    meal_options_count = serializers.IntegerField()
    total_reservations = serializers.IntegerField()
    reserved_count = serializers.IntegerField()
    cancelled_count = serializers.IntegerField()
    served_count = serializers.IntegerField()
    total_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    meal_options = MealOptionReportSerializer(many=True, read_only=True)


class UserReportSerializer(serializers.Serializer):
    """سریالایزر گزارش بر اساس کاربر"""
    user_id = serializers.IntegerField()
    username = serializers.CharField()
    full_name = serializers.CharField()
    employee_number = serializers.CharField()
    center_name = serializers.CharField()
    total_reservations = serializers.IntegerField()
    total_guest_reservations = serializers.IntegerField()
    reserved_count = serializers.IntegerField()
    cancelled_count = serializers.IntegerField()
    served_count = serializers.IntegerField()
    total_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    reserved_amount = serializers.DecimalField(max_digits=10, decimal_places=2)


class DateReportSerializer(serializers.Serializer):
    """سریالایزر گزارش بر اساس تاریخ"""
    date = serializers.DateField()
    jalali_date = serializers.CharField()
    total_reservations = serializers.IntegerField()
    total_guest_reservations = serializers.IntegerField()
    reserved_count = serializers.IntegerField()
    cancelled_count = serializers.IntegerField()
    served_count = serializers.IntegerField()
    total_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    reserved_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    centers = serializers.ListField(child=serializers.DictField())


class DetailedReservationReportSerializer(serializers.ModelSerializer):
    """سریالایزر جزئیات رزرو برای گزارش"""
    user_name = serializers.CharField(source='user.username', read_only=True)
    user_full_name = serializers.CharField(source='user.get_full_name', read_only=True)
    employee_number = serializers.CharField(source='user.employee_number', read_only=True)
    center_name = serializers.CharField(source='daily_menu.center.name', read_only=True)
    meal_option_title = serializers.CharField(source='meal_option.title', read_only=True)
    base_meal_title = serializers.CharField(source='meal_option.base_meal.title', read_only=True)
    restaurant_name = serializers.SerializerMethodField()
    date = serializers.SerializerMethodField()
    jalali_date = serializers.SerializerMethodField()
    jalali_reservation_date = serializers.SerializerMethodField()
    
    class Meta:
        model = FoodReservation
        fields = [
            'id', 'user', 'user_name', 'user_full_name', 'employee_number',
            'center_name', 'meal_option', 'meal_option_title', 'base_meal_title',
            'restaurant_name', 'quantity', 'amount',
            'status', 'date', 'jalali_date', 'reservation_date',
            'jalali_reservation_date', 'cancelled_at'
        ]
    
    def get_date(self, obj):
        """تاریخ از daily_menu"""
        if obj.daily_menu and obj.daily_menu.date:
            return obj.daily_menu.date
        return None
    
    def get_restaurant_name(self, obj):
        if obj.meal_option and obj.meal_option.restaurant:
            return obj.meal_option.restaurant.name
        return None
    
    def get_jalali_date(self, obj):
        if obj.daily_menu and obj.daily_menu.date:
            jalali_date = jdatetime.date.fromgregorian(date=obj.daily_menu.date)
            return jalali_date.strftime('%Y/%m/%d')
        return None
    
    def get_jalali_reservation_date(self, obj):
        if obj.reservation_date:
            jalali_datetime = jdatetime.datetime.fromgregorian(datetime=obj.reservation_date)
            return jalali_datetime.strftime('%Y/%m/%d %H:%M')
        return None


class ComprehensiveReportSerializer(serializers.Serializer):
    """سریالایزر گزارش جامع"""
    total_reservations = serializers.IntegerField()
    total_guest_reservations = serializers.IntegerField()
    total_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    reserved_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    served_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    cancelled_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    by_meal_option = MealOptionReportSerializer(many=True)
    by_base_meal = BaseMealReportSerializer(many=True)
    by_user = UserReportSerializer(many=True)
    by_date = DateReportSerializer(many=True)

