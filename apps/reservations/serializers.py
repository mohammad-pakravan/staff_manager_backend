"""
Serializers for reservations app
"""
from rest_framework import serializers
from django.utils import timezone
from drf_spectacular.utils import extend_schema_field
from datetime import datetime
from jalali_date import datetime2jalali, date2jalali
from apps.food_management.models import (
    FoodReservation, GuestReservation, BaseMeal, DailyMenuMealOption,
    DessertReservation, GuestDessertReservation, BaseDessert, DailyMenuDessertOption,
    DailyMenu
)
# برای سازگاری با کدهای قبلی
Dessert = BaseDessert
# Import from meals app
from apps.meals.serializers import (
    BaseMealSerializer, DailyMenuSerializer, DailyMenuMealOptionSerializer,
    BaseMealWithOptionsSerializer, SimpleMealOptionSerializer,
    BaseDessertSerializer, SimpleBaseDessertSerializer, DailyMenuDessertOptionSerializer
)
# برای سازگاری با کدهای قبلی
DessertSerializer = BaseDessertSerializer
SimpleDessertSerializer = SimpleBaseDessertSerializer
# برای سازگاری با کدهای قبلی
Meal = BaseMeal
MealSerializer = BaseMealSerializer


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
            # cancellation_deadline اکنون string است
            if obj.cancellation_deadline:
                return None  # یا می‌توانید منطق مقایسه تاریخ شمسی را اضافه کنید
            return "مهلت لغو گذشته"
        return None

    @extend_schema_field(serializers.CharField())
    def get_jalali_reservation_date(self, obj):
        if obj.reservation_date:
            return datetime2jalali(obj.reservation_date).strftime('%Y/%m/%d %H:%M')
        return None

    @extend_schema_field(serializers.CharField())
    def get_jalali_cancellation_deadline(self, obj):
        if obj.cancellation_deadline:
            return str(obj.cancellation_deadline)
        return None

    @extend_schema_field(serializers.CharField())
    def get_jalali_cancelled_at(self, obj):
        if obj.cancelled_at:
            return datetime2jalali(obj.cancelled_at).strftime('%Y/%m/%d %H:%M')
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
                queryset=DailyMenuMealOption.objects.all(),
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
            return datetime2jalali(obj.reservation_date).strftime('%Y/%m/%d %H:%M')
        return None


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
            'daily_menu', 'meal', 'description', 'amount', 'reservation_date', 'jalali_reservation_date', 
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
            # cancellation_deadline اکنون string است
            if obj.cancellation_deadline:
                return None  # یا می‌توانید منطق مقایسه تاریخ شمسی را اضافه کنید
            return "مهلت لغو گذشته"
        return None

    @extend_schema_field(serializers.CharField())
    def get_jalali_reservation_date(self, obj):
        if obj.reservation_date:
            return datetime2jalali(obj.reservation_date).strftime('%Y/%m/%d %H:%M')
        return None

    @extend_schema_field(serializers.CharField())
    def get_jalali_cancellation_deadline(self, obj):
        if obj.cancellation_deadline:
            return str(obj.cancellation_deadline)
        return None

    @extend_schema_field(serializers.CharField())
    def get_jalali_cancelled_at(self, obj):
        if obj.cancelled_at:
            return datetime2jalali(obj.cancelled_at).strftime('%Y/%m/%d %H:%M')
        return None


class GuestReservationCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating GuestReservation"""
    meal = serializers.PrimaryKeyRelatedField(read_only=True, required=False, allow_null=True)  # برای سازگاری
    
    class Meta:
        model = GuestReservation
        fields = ['guest_first_name', 'guest_last_name', 'daily_menu', 'meal_option', 'meal', 'description']

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
                queryset=DailyMenuMealOption.objects.all(),
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


class SimpleGuestReservationSerializer(serializers.ModelSerializer):
    """سریالایزر ساده برای رزرو مهمان - فقط اطلاعات ضروری"""
    meal = serializers.SerializerMethodField()  # BaseMeal با meal_option داخلش
    guest_full_name = serializers.SerializerMethodField()
    jalali_reservation_date = serializers.SerializerMethodField()
    
    class Meta:
        model = GuestReservation
        fields = [
            'id', 'guest_first_name', 'guest_last_name', 'guest_full_name',
            'meal', 'description', 'status', 'reservation_date', 'jalali_reservation_date'
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
            return datetime2jalali(obj.reservation_date).strftime('%Y/%m/%d %H:%M')
        return None


# ========== Dessert Reservation Serializers ==========

class DessertReservationSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.username', read_only=True)
    user_full_name = serializers.SerializerMethodField()
    dessert_option_detail = DailyMenuDessertOptionSerializer(source='dessert_option', read_only=True)
    daily_menu = DailyMenuSerializer(read_only=True)
    can_cancel = serializers.SerializerMethodField()
    time_until_cancellation = serializers.SerializerMethodField()
    jalali_reservation_date = serializers.SerializerMethodField()
    jalali_cancellation_deadline = serializers.SerializerMethodField()
    jalali_cancelled_at = serializers.SerializerMethodField()

    class Meta:
        model = DessertReservation
        fields = [
            'id', 'user', 'user_name', 'user_full_name', 'daily_menu', 'dessert_option', 'dessert_option_detail', 
            'quantity', 'amount',
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
            # cancellation_deadline اکنون string است
            if obj.cancellation_deadline:
                return None  # یا می‌توانید منطق مقایسه تاریخ شمسی را اضافه کنید
            return "مهلت لغو گذشته"
        return None

    @extend_schema_field(serializers.CharField())
    def get_jalali_reservation_date(self, obj):
        if obj.reservation_date:
            return datetime2jalali(obj.reservation_date).strftime('%Y/%m/%d %H:%M')
        return None

    @extend_schema_field(serializers.CharField())
    def get_jalali_cancellation_deadline(self, obj):
        if obj.cancellation_deadline:
            return str(obj.cancellation_deadline)
        return None

    @extend_schema_field(serializers.CharField())
    def get_jalali_cancelled_at(self, obj):
        if obj.cancelled_at:
            return datetime2jalali(obj.cancelled_at).strftime('%Y/%m/%d %H:%M')
        return None


class DessertReservationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = DessertReservation
        fields = ['daily_menu', 'dessert_option', 'quantity']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['dessert_option'] = serializers.PrimaryKeyRelatedField(
            queryset=DailyMenuDessertOption.objects.all(),
            required=True
        )

    def validate(self, data):
        daily_menu = data.get('daily_menu')
        dessert_option = data.get('dessert_option')
        quantity = data.get('quantity', 1)
        
        # اگر در حال update هستیم، dessert_option و daily_menu را از instance بگیریم
        if self.instance:
            if 'dessert_option' not in data:
                dessert_option = self.instance.dessert_option
            if 'daily_menu' not in data:
                daily_menu = self.instance.daily_menu
            if 'quantity' not in data:
                quantity = self.instance.quantity
        
        if dessert_option and daily_menu:
            # بررسی اینکه دسر در منوی روزانه موجود است
            if dessert_option.daily_menu != daily_menu:
                raise serializers.ValidationError({
                    'dessert_option': 'گزینه دسر باید متعلق به منوی روزانه انتخاب شده باشد'
                })
            
            # بررسی قیمت
            if dessert_option.price <= 0:
                raise serializers.ValidationError({
                    'dessert_option': 'قیمت دسر باید بیشتر از صفر باشد'
                })
            
            # بررسی موجودی
            # اگر در حال update هستیم، quantity قبلی را از reserved_quantity کم می‌کنیم
            available_quantity = dessert_option.available_quantity
            if self.instance and self.instance.status == 'reserved':
                # اگر رزرو فعال است، quantity قبلی را به موجودی اضافه می‌کنیم
                available_quantity += self.instance.quantity
            
            if available_quantity < quantity:
                raise serializers.ValidationError({
                    'quantity': f'موجودی کافی نیست. موجودی: {available_quantity}'
                })
        
        return data

    def create(self, validated_data):
        user = self.context['request'].user
        daily_menu = validated_data['daily_menu']
        dessert_option = validated_data['dessert_option']
        quantity = validated_data.get('quantity', 1)
        
        # محدودیت رزرو برای کاربران برداشته شده است
        # کاربران می‌توانند نامحدود رزرو کنند (فقط موجودی چک می‌شود)
        
        # بررسی قیمت
        if dessert_option.price <= 0:
            raise serializers.ValidationError({
                'dessert_option': 'قیمت دسر باید بیشتر از صفر باشد'
            })
        
        # محاسبه مبلغ
        amount = dessert_option.price * quantity
        
        reservation = DessertReservation.objects.create(
            user=user,
            daily_menu=daily_menu,
            dessert_option=dessert_option,
            quantity=quantity,
            amount=amount
        )
        
        # به‌روزرسانی reserved_quantity
        dessert_option.reserved_quantity += quantity
        dessert_option.save()
        
        return reservation
    
    def update(self, instance, validated_data):
        """به‌روزرسانی رزرو دسر"""
        dessert_option = validated_data.get('dessert_option', instance.dessert_option)
        quantity = validated_data.get('quantity', instance.quantity)
        
        # بررسی قیمت
        if dessert_option.price <= 0:
            raise serializers.ValidationError({
                'dessert_option': 'قیمت دسر باید بیشتر از صفر باشد'
            })
        
        # اگر quantity یا dessert_option تغییر کرده است
        old_quantity = instance.quantity if instance.status == 'reserved' else 0
        new_quantity = quantity
        
        # به‌روزرسانی reserved_quantity
        if old_quantity != new_quantity or instance.dessert_option != dessert_option:
            # اگر dessert_option تغییر کرده، quantity قبلی را از dessert_option قبلی کم می‌کنیم
            if instance.dessert_option and instance.dessert_option != dessert_option and instance.status == 'reserved':
                instance.dessert_option.reserved_quantity = max(0, instance.dessert_option.reserved_quantity - old_quantity)
                instance.dessert_option.save()
            
            # quantity جدید را اضافه می‌کنیم
            if instance.status == 'reserved':
                dessert_option.reserved_quantity = dessert_option.reserved_quantity - old_quantity + new_quantity
            else:
                dessert_option.reserved_quantity += new_quantity
            dessert_option.save()
        
        # محاسبه مبلغ جدید
        validated_data['amount'] = dessert_option.price * quantity
        
        return super().update(instance, validated_data)


class CombinedReservationCreateSerializer(serializers.Serializer):
    """سریالایزر یکپارچه برای رزرو غذا و دسر"""
    daily_menu = serializers.PrimaryKeyRelatedField(
        queryset=DailyMenu.objects.all(),
        required=True
    )
    base_meal = serializers.IntegerField(required=False, allow_null=True)
    meal_option = serializers.PrimaryKeyRelatedField(
        queryset=DailyMenuMealOption.objects.all(),
        required=False,
        allow_null=True
    )
    meal_quantity = serializers.IntegerField(min_value=1, required=False, allow_null=True)
    dessert = serializers.IntegerField(required=False, allow_null=True)
    dessert_option = serializers.PrimaryKeyRelatedField(
        queryset=DailyMenuDessertOption.objects.all(),
        required=False,
        allow_null=True
    )
    dessert_quantity = serializers.IntegerField(min_value=1, required=False, allow_null=True)
    quantity = serializers.IntegerField(min_value=1, required=False, allow_null=True)
    
    def validate(self, data):
        daily_menu = data.get('daily_menu')
        meal_option = data.get('meal_option')
        dessert_option = data.get('dessert_option')

        # map کردن quantity به meal_quantity یا dessert_quantity
        quantity = data.get('quantity')
        if quantity is not None:
            if meal_option and not data.get('meal_quantity'):
                data['meal_quantity'] = quantity
            if dessert_option and not data.get('dessert_quantity'):
                data['dessert_quantity'] = quantity

        meal_quantity = data.get('meal_quantity', 1)
        dessert_quantity = data.get('dessert_quantity', 1)
        
        # حداقل یکی از meal_option یا dessert_option باید وجود داشته باشد
        if not meal_option and not dessert_option:
            raise serializers.ValidationError({
                'error': 'حداقل یکی از meal_option یا dessert_option باید انتخاب شود'
            })
        
        # بررسی meal_option
        if meal_option:
            if meal_option.daily_menu != daily_menu:
                raise serializers.ValidationError({
                    'meal_option': 'گزینه غذا باید متعلق به منوی روزانه انتخاب شده باشد'
                })
            
            if meal_option.price <= 0:
                raise serializers.ValidationError({
                    'meal_option': 'قیمت غذا باید بیشتر از صفر باشد'
                })
            
            available_quantity = meal_option.available_quantity
            if available_quantity < meal_quantity:
                raise serializers.ValidationError({
                    'meal_quantity': f'موجودی کافی نیست. موجودی: {available_quantity}'
                })
        
        # بررسی dessert_option
        if dessert_option:
            if dessert_option.daily_menu != daily_menu:
                raise serializers.ValidationError({
                    'dessert_option': 'گزینه دسر باید متعلق به منوی روزانه انتخاب شده باشد'
                })
            
            if dessert_option.price <= 0:
                raise serializers.ValidationError({
                    'dessert_option': 'قیمت دسر باید بیشتر از صفر باشد'
                })
            
            available_quantity = dessert_option.available_quantity
            if available_quantity < dessert_quantity:
                raise serializers.ValidationError({
                    'dessert_quantity': f'موجودی کافی نیست. موجودی: {available_quantity}'
                })
        
        return data
    
    def create(self, validated_data):
        user = self.context['request'].user
        daily_menu = validated_data['daily_menu']
        meal_option = validated_data.get('meal_option')
        dessert_option = validated_data.get('dessert_option')
        meal_quantity = validated_data.get('meal_quantity', 1)
        dessert_quantity = validated_data.get('dessert_quantity', 1)
        
        results = {
            'meal_reservation': None,
            'dessert_reservation': None
        }
        
        # ایجاد رزرو غذا
        if meal_option:
            amount = meal_option.price * meal_quantity
            meal_reservation = FoodReservation.objects.create(
                user=user,
                daily_menu=daily_menu,
                meal_option=meal_option,
                quantity=meal_quantity,
                amount=amount
            )
            meal_option.reserved_quantity += meal_quantity
            meal_option.save()
            results['meal_reservation'] = meal_reservation
        
        # ایجاد رزرو دسر
        if dessert_option:
            amount = dessert_option.price * dessert_quantity
            dessert_reservation = DessertReservation.objects.create(
                user=user,
                daily_menu=daily_menu,
                dessert_option=dessert_option,
                quantity=dessert_quantity,
                amount=amount
            )
            dessert_option.reserved_quantity += dessert_quantity
            dessert_option.save()
            results['dessert_reservation'] = dessert_reservation
        
        return results


class CombinedGuestReservationCreateSerializer(serializers.Serializer):
    """سریالایزر یکپارچه برای رزرو غذا و دسر"""
    daily_menu = serializers.PrimaryKeyRelatedField(
        queryset=DailyMenu.objects.all(),
        required=True
    )
    guest_first_name = serializers.CharField(
        required=True,
        max_length=100,
        help_text="نام میهمان"
    )
    guest_last_name = serializers.CharField(
        required=True,
        max_length=100,
        help_text="نام خانوادگی میهمان"
    )
    base_meal = serializers.IntegerField(required=False, allow_null=True)
    meal_option = serializers.PrimaryKeyRelatedField(
        queryset=DailyMenuMealOption.objects.all(),
        required=False,
        allow_null=True
    )
    meal_quantity = serializers.IntegerField(min_value=1, required=False, allow_null=True)
    dessert = serializers.IntegerField(required=False, allow_null=True)
    dessert_option = serializers.PrimaryKeyRelatedField(
        queryset=DailyMenuDessertOption.objects.all(),
        required=False,
        allow_null=True
    )
    dessert_quantity = serializers.IntegerField(min_value=1, required=False, allow_null=True)
    quantity = serializers.IntegerField(min_value=1, required=False, allow_null=True)
    description = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
        help_text="توضیحات اضافی برای رزرو"
    )

    def validate(self, data):
        daily_menu = data.get('daily_menu')
        meal_option = data.get('meal_option')
        dessert_option = data.get('dessert_option')

        # map کردن quantity به meal_quantity یا dessert_quantity
        quantity = data.get('quantity')
        if quantity is not None:
            if meal_option and not data.get('meal_quantity'):
                data['meal_quantity'] = quantity
            if dessert_option and not data.get('dessert_quantity'):
                data['dessert_quantity'] = quantity

        meal_quantity = data.get('meal_quantity', 1)
        dessert_quantity = data.get('dessert_quantity', 1)
        
        # حداقل یکی از meal_option یا dessert_option باید وجود داشته باشد
        if not meal_option and not dessert_option:
            raise serializers.ValidationError({
                'error': 'حداقل یکی از meal_option یا dessert_option باید انتخاب شود'
            })
        
        # بررسی meal_option
        if meal_option:
            if meal_option.daily_menu != daily_menu:
                raise serializers.ValidationError({
                    'meal_option': 'گزینه غذا باید متعلق به منوی روزانه انتخاب شده باشد'
                })
            
            if meal_option.price <= 0:
                raise serializers.ValidationError({
                    'meal_option': 'قیمت غذا باید بیشتر از صفر باشد'
                })
            
            available_quantity = meal_option.available_quantity
            if available_quantity < meal_quantity:
                raise serializers.ValidationError({
                    'meal_quantity': f'موجودی کافی نیست. موجودی: {available_quantity}'
                })
        
        # بررسی dessert_option
        if dessert_option:
            if dessert_option.daily_menu != daily_menu:
                raise serializers.ValidationError({
                    'dessert_option': 'گزینه دسر باید متعلق به منوی روزانه انتخاب شده باشد'
                })
            
            if dessert_option.price <= 0:
                raise serializers.ValidationError({
                    'dessert_option': 'قیمت دسر باید بیشتر از صفر باشد'
                })
            
            available_quantity = dessert_option.available_quantity
            if available_quantity < dessert_quantity:
                raise serializers.ValidationError({
                    'dessert_quantity': f'موجودی کافی نیست. موجودی: {available_quantity}'
                })
        
        return data
    
    def create(self, validated_data):
        user = self.context['request'].user
        
        # استخراج اطلاعات میهمان از validated_data
        guest_first_name = validated_data.pop('guest_first_name')
        guest_last_name = validated_data.pop('guest_last_name')
        description = validated_data.pop('description', None)
        
        daily_menu = validated_data['daily_menu']
        meal_option = validated_data.get('meal_option')
        dessert_option = validated_data.get('dessert_option')
        meal_quantity = validated_data.get('meal_quantity', 1)
        dessert_quantity = validated_data.get('dessert_quantity', 1)
        
        results = {
            'meal_reservation': None,
            'dessert_reservation': None
        }
        
        # ایجاد رزرو غذا
        if meal_option:
            amount = meal_option.price * meal_quantity
            meal_reservation = GuestReservation.objects.create(
                host_user=user,
                guest_first_name=guest_first_name,
                guest_last_name=guest_last_name,
                daily_menu=daily_menu,
                meal_option=meal_option,
                amount=amount,
                description=description
            )
            meal_option.reserved_quantity += meal_quantity
            meal_option.save()
            results['meal_reservation'] = meal_reservation
        
        # ایجاد رزرو دسر
        if dessert_option:
            amount = dessert_option.price * dessert_quantity
            dessert_reservation = GuestDessertReservation.objects.create(
                host_user=user,
                guest_first_name=guest_first_name,
                guest_last_name=guest_last_name,
                daily_menu=daily_menu,
                dessert_option=dessert_option,
                amount=amount
            )
            dessert_option.reserved_quantity += dessert_quantity
            dessert_option.save()
            results['dessert_reservation'] = dessert_reservation
        
        return results

class CombinedGuestReservationResponseSerializer(serializers.Serializer):
    message = serializers.CharField(default='رزرو با موفقیت ایجاد شد')
    meal_reservation = serializers.SerializerMethodField()
    dessert_reservation = serializers.SerializerMethodField()
    
    def get_meal_reservation(self, obj):
        meal_reservation = obj.get('meal_reservation')
        if not meal_reservation:
            return None
        
        return {
            'id': meal_reservation.id,
            'type': 'meal',
            'guest_name': f"{meal_reservation.guest_first_name} {meal_reservation.guest_last_name}",
            'meal_option': meal_reservation.meal_option.title if meal_reservation.meal_option else None,
            'amount': str(meal_reservation.amount),
        }
    
    def get_dessert_reservation(self, obj):
        dessert_reservation = obj.get('dessert_reservation')
        if not dessert_reservation:
            return None
        
        return {
            'id': dessert_reservation.id,
            'type': 'dessert',
            'guest_name': f"{dessert_reservation.guest_first_name} {dessert_reservation.guest_last_name}",
            'dessert_option': dessert_reservation.dessert_option.title if dessert_reservation.dessert_option else None,
            'amount': str(dessert_reservation.amount),
        }

class CombinedReservationUpdateSerializer(serializers.Serializer):
    """سریالایزر برای به‌روزرسانی رزرو یکپارچه غذا و دسر"""
    meal_reservation_id = serializers.IntegerField(required=False, allow_null=True)
    dessert_reservation_id = serializers.IntegerField(required=False, allow_null=True)
    
    # فیلدهای به‌روزرسانی برای meal reservation
    daily_menu = serializers.PrimaryKeyRelatedField(
        queryset=DailyMenu.objects.all(),
        required=False,
        allow_null=True
    )
    meal_option = serializers.PrimaryKeyRelatedField(
        queryset=DailyMenuMealOption.objects.all(),
        required=False,
        allow_null=True
    )
    meal_quantity = serializers.IntegerField(min_value=1, required=False)
    
    # فیلدهای به‌روزرسانی برای dessert reservation
    dessert_option = serializers.PrimaryKeyRelatedField(
        queryset=DailyMenuDessertOption.objects.all(),
        required=False,
        allow_null=True
    )
    dessert_quantity = serializers.IntegerField(min_value=1, required=False)
    
    def validate(self, data):
        meal_reservation_id = data.get('meal_reservation_id')
        dessert_reservation_id = data.get('dessert_reservation_id')
        meal_option = data.get('meal_option')
        dessert_option = data.get('dessert_option')
        meal_quantity = data.get('meal_quantity')
        dessert_quantity = data.get('dessert_quantity')
        daily_menu = data.get('daily_menu')
        
        # حداقل یکی از reservation_id ها باید وجود داشته باشد
        if not meal_reservation_id and not dessert_reservation_id:
            raise serializers.ValidationError({
                'error': 'حداقل یکی از meal_reservation_id یا dessert_reservation_id باید ارسال شود'
            })
        
        # اگر meal_reservation_id وجود دارد، باید meal_option و meal_quantity هم ارسال شود
        if meal_reservation_id:
            if not meal_option:
                raise serializers.ValidationError({
                    'meal_option': 'برای به‌روزرسانی رزرو غذا، meal_option الزامی است'
                })
            if meal_quantity is None:
                raise serializers.ValidationError({
                    'meal_quantity': 'برای به‌روزرسانی رزرو غذا، meal_quantity الزامی است'
                })
            if not daily_menu:
                raise serializers.ValidationError({
                    'daily_menu': 'برای به‌روزرسانی رزرو غذا، daily_menu الزامی است'
                })
            
            # بررسی meal_option
            if meal_option.daily_menu != daily_menu:
                raise serializers.ValidationError({
                    'meal_option': 'گزینه غذا باید متعلق به منوی روزانه انتخاب شده باشد'
                })
            
            # بررسی موجودی
            available_quantity = meal_option.available_quantity
            # اگر در حال به‌روزرسانی هستیم و meal_option همان است، باید رزرو فعلی را از محاسبه کم کنیم
            try:
                current_reservation = FoodReservation.objects.get(id=meal_reservation_id)
                if current_reservation.status == 'reserved' and current_reservation.meal_option and current_reservation.meal_option.id == meal_option.id:
                    available_quantity += current_reservation.quantity
            except FoodReservation.DoesNotExist:
                pass
            
            if available_quantity < meal_quantity:
                raise serializers.ValidationError({
                    'meal_quantity': f'موجودی کافی نیست. موجودی: {available_quantity}'
                })
        
        # اگر dessert_reservation_id وجود دارد، باید dessert_option و dessert_quantity هم ارسال شود
        if dessert_reservation_id:
            if not dessert_option:
                raise serializers.ValidationError({
                    'dessert_option': 'برای به‌روزرسانی رزرو دسر، dessert_option الزامی است'
                })
            if dessert_quantity is None:
                raise serializers.ValidationError({
                    'dessert_quantity': 'برای به‌روزرسانی رزرو دسر، dessert_quantity الزامی است'
                })
            if not daily_menu:
                raise serializers.ValidationError({
                    'daily_menu': 'برای به‌روزرسانی رزرو دسر، daily_menu الزامی است'
                })
            
            # بررسی dessert_option
            if dessert_option.daily_menu != daily_menu:
                raise serializers.ValidationError({
                    'dessert_option': 'گزینه دسر باید متعلق به منوی روزانه انتخاب شده باشد'
                })
            
            # بررسی موجودی
            available_quantity = dessert_option.available_quantity
            # اگر در حال به‌روزرسانی هستیم و dessert_option همان است، باید رزرو فعلی را از محاسبه کم کنیم
            try:
                current_reservation = DessertReservation.objects.get(id=dessert_reservation_id)
                if current_reservation.status == 'reserved' and current_reservation.dessert_option and current_reservation.dessert_option.id == dessert_option.id:
                    available_quantity += current_reservation.quantity
            except DessertReservation.DoesNotExist:
                pass
            
            if available_quantity < dessert_quantity:
                raise serializers.ValidationError({
                    'dessert_quantity': f'موجودی کافی نیست. موجودی: {available_quantity}'
                })
        
        return data


class CombinedReservationResponseSerializer(serializers.Serializer):
    """سریالایزر ساده برای خروجی combined reservations"""
    meal_reservation = serializers.SerializerMethodField()
    dessert_reservation = serializers.SerializerMethodField()
    
    def get_meal_reservation(self, obj):
        """ساختار ساده برای meal reservation"""
        meal_reservation = obj.get('meal_reservation')
        if not meal_reservation:
            return None
        
        meal_option = meal_reservation.meal_option
        if not meal_option:
            return None
        
        daily_menu = meal_reservation.daily_menu
        
        return {
            'id': meal_reservation.id,
            'daily_menu': {
                'id': daily_menu.id if daily_menu else None,
                'date': str(daily_menu.date) if daily_menu and daily_menu.date else None,
                'jalali_date': date2jalali(daily_menu.date).strftime('%Y/%m/%d') if daily_menu and daily_menu.date else None,
                'restaurant': {
                    'id': daily_menu.restaurant.id if daily_menu and daily_menu.restaurant else None,
                    'name': daily_menu.restaurant.name if daily_menu and daily_menu.restaurant else None,
                } if daily_menu and daily_menu.restaurant else None,
            } if daily_menu else None,
            'meal_option': {
                'id': meal_option.id,
                'title': meal_option.title,
                'price': float(meal_option.price) if meal_option.price else 0.0,
            },
            'base_meal': {
                'id': meal_option.base_meal.id if meal_option.base_meal else None,
                'title': meal_option.base_meal.title if meal_option.base_meal else None,
            } if meal_option.base_meal else None,
            'quantity': meal_reservation.quantity,
            'status': meal_reservation.status,
            'amount': float(meal_reservation.amount) if meal_reservation.amount else 0.0,
            'reservation_date': meal_reservation.reservation_date.isoformat() if meal_reservation.reservation_date else None,
            'jalali_reservation_date': datetime2jalali(meal_reservation.reservation_date).strftime('%Y/%m/%d %H:%M') if meal_reservation.reservation_date else None,
        }
    
    def get_dessert_reservation(self, obj):
        """ساختار ساده برای dessert reservation"""
        dessert_reservation = obj.get('dessert_reservation')
        if not dessert_reservation:
            return None
        
        dessert_option = dessert_reservation.dessert_option
        if not dessert_option:
            return None
        
        daily_menu = dessert_reservation.daily_menu
        
        return {
            'id': dessert_reservation.id,
            'daily_menu': {
                'id': daily_menu.id if daily_menu else None,
                'date': str(daily_menu.date) if daily_menu and daily_menu.date else None,
                'jalali_date': date2jalali(daily_menu.date).strftime('%Y/%m/%d') if daily_menu and daily_menu.date else None,
                'restaurant': {
                    'id': daily_menu.restaurant.id if daily_menu and daily_menu.restaurant else None,
                    'name': daily_menu.restaurant.name if daily_menu and daily_menu.restaurant else None,
                } if daily_menu and daily_menu.restaurant else None,
            } if daily_menu else None,
            'dessert_option': {
                'id': dessert_option.id,
                'title': dessert_option.title,
                'price': float(dessert_option.price) if dessert_option.price else 0.0,
            },
            'base_dessert': {
                'id': dessert_option.base_dessert.id if dessert_option.base_dessert else None,
                'title': dessert_option.base_dessert.title if dessert_option.base_dessert else None,
            } if dessert_option.base_dessert else None,
            'quantity': dessert_reservation.quantity,
            'status': dessert_reservation.status,
            'amount': float(dessert_reservation.amount) if dessert_reservation.amount else 0.0,
            'reservation_date': dessert_reservation.reservation_date.isoformat() if dessert_reservation.reservation_date else None,
            'jalali_reservation_date': datetime2jalali(dessert_reservation.reservation_date).strftime('%Y/%m/%d %H:%M') if dessert_reservation.reservation_date else None,
        }


class SimpleDessertReservationSerializer(serializers.ModelSerializer):
    """سریالایزر ساده برای رزرو دسر - فقط اطلاعات ضروری"""
    dessert_option_title = serializers.SerializerMethodField()
    title = serializers.SerializerMethodField()
    image_url = serializers.SerializerMethodField()
    user_name = serializers.CharField(source='user.username', read_only=True)
    jalali_reservation_date = serializers.SerializerMethodField()
    
    class Meta:
        model = DessertReservation
        fields = [
            'id', 'user', 'user_name', 'dessert_option', 'dessert_option_title', 'title',
            'image_url', 'quantity', 'status', 'amount', 'reservation_date', 'jalali_reservation_date'
        ]
        read_only_fields = ['reservation_date']

    @extend_schema_field(serializers.CharField())
    def get_dessert_option_title(self, obj):
        if obj.dessert_option:
            return obj.dessert_option.title
        elif obj.dessert_option_info:
            return obj.dessert_option_info
        return "بدون دسر"
    
    @extend_schema_field(serializers.CharField())
    def get_title(self, obj):
        """برگرداندن عنوان دسر پایه - برای سازگاری و سهولت استفاده"""
        if obj.dessert_option and obj.dessert_option.base_dessert:
            return obj.dessert_option.base_dessert.title
        elif obj.dessert_option_info:
            return obj.dessert_option_info
        return "بدون دسر"
    
    @extend_schema_field(serializers.CharField())
    def get_image_url(self, obj):
        """برگرداندن URL تصویر دسر"""
        if obj.dessert_option and obj.dessert_option.base_dessert and obj.dessert_option.base_dessert.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.dessert_option.base_dessert.image.url)
            return obj.dessert_option.base_dessert.image.url
        return None

    @extend_schema_field(serializers.CharField())
    def get_jalali_reservation_date(self, obj):
        if obj.reservation_date:
            return datetime2jalali(obj.reservation_date).strftime('%Y/%m/%d %H:%M')
        return None


class GuestDessertReservationSerializer(serializers.ModelSerializer):
    host_user_name = serializers.CharField(source='host_user.username', read_only=True)
    host_user_full_name = serializers.SerializerMethodField()
    guest_full_name = serializers.SerializerMethodField()
    dessert_option_detail = DailyMenuDessertOptionSerializer(source='dessert_option', read_only=True)
    daily_menu = DailyMenuSerializer(read_only=True)
    can_cancel = serializers.SerializerMethodField()
    time_until_cancellation = serializers.SerializerMethodField()
    jalali_reservation_date = serializers.SerializerMethodField()
    jalali_cancellation_deadline = serializers.SerializerMethodField()
    jalali_cancelled_at = serializers.SerializerMethodField()

    class Meta:
        model = GuestDessertReservation
        fields = [
            'id', 'host_user', 'host_user_name', 'host_user_full_name',
            'guest_first_name', 'guest_last_name', 'guest_full_name',
            'daily_menu', 'dessert_option', 'dessert_option_detail', 'status', 'amount',
            'reservation_date', 'jalali_reservation_date', 'cancellation_deadline', 
            'jalali_cancellation_deadline', 'cancelled_at', 'jalali_cancelled_at',
            'can_cancel', 'time_until_cancellation'
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
            # cancellation_deadline اکنون string است
            if obj.cancellation_deadline:
                return None  # یا می‌توانید منطق مقایسه تاریخ شمسی را اضافه کنید
            return "مهلت لغو گذشته"
        return None

    @extend_schema_field(serializers.CharField())
    def get_jalali_reservation_date(self, obj):
        if obj.reservation_date:
            return datetime2jalali(obj.reservation_date).strftime('%Y/%m/%d %H:%M')
        return None

    @extend_schema_field(serializers.CharField())
    def get_jalali_cancellation_deadline(self, obj):
        if obj.cancellation_deadline:
            return str(obj.cancellation_deadline)
        return None

    @extend_schema_field(serializers.CharField())
    def get_jalali_cancelled_at(self, obj):
        if obj.cancelled_at:
            return datetime2jalali(obj.cancelled_at).strftime('%Y/%m/%d %H:%M')
        return None


class GuestDessertReservationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = GuestDessertReservation
        fields = ['daily_menu', 'dessert_option', 'guest_first_name', 'guest_last_name']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['dessert_option'] = serializers.PrimaryKeyRelatedField(
            queryset=DailyMenuDessertOption.objects.all(),
            required=True
        )

    def validate(self, data):
        daily_menu = data.get('daily_menu')
        dessert_option = data.get('dessert_option')
        
        # اگر در حال update هستیم، dessert_option و daily_menu را از instance بگیریم
        if self.instance:
            if 'dessert_option' not in data:
                dessert_option = self.instance.dessert_option
            if 'daily_menu' not in data:
                daily_menu = self.instance.daily_menu
        
        if dessert_option and daily_menu:
            # بررسی اینکه دسر در منوی روزانه موجود است
            if dessert_option.daily_menu != daily_menu:
                raise serializers.ValidationError({
                    'dessert_option': 'گزینه دسر باید متعلق به منوی روزانه انتخاب شده باشد'
                })
            
            # بررسی قیمت
            if dessert_option.price <= 0:
                raise serializers.ValidationError({
                    'dessert_option': 'قیمت دسر باید بیشتر از صفر باشد'
                })
            
            # بررسی موجودی
            # اگر در حال update هستیم و رزرو فعال است، quantity قبلی را به موجودی اضافه می‌کنیم
            available_quantity = dessert_option.available_quantity
            if self.instance and self.instance.status == 'reserved':
                available_quantity += 1  # رزرو مهمان همیشه 1 است
            
            if available_quantity < 1:
                raise serializers.ValidationError({
                    'dessert_option': f'موجودی کافی نیست. موجودی: {available_quantity}'
                })
        
        return data

    def create(self, validated_data):
        user = self.context['request'].user
        daily_menu = validated_data['daily_menu']
        dessert_option = validated_data['dessert_option']
        
        # محدودیت رزرو برای کاربران برداشته شده است
        # کاربران می‌توانند نامحدود رزرو کنند (فقط موجودی چک می‌شود)
        
        # بررسی قیمت
        if dessert_option.price <= 0:
            raise serializers.ValidationError({
                'dessert_option': 'قیمت دسر باید بیشتر از صفر باشد'
            })
        
        # محاسبه مبلغ
        amount = dessert_option.price
        
        reservation = GuestDessertReservation.objects.create(
            host_user=user,
            daily_menu=daily_menu,
            dessert_option=dessert_option,
            guest_first_name=validated_data['guest_first_name'],
            guest_last_name=validated_data['guest_last_name'],
            amount=amount
        )
        
        # به‌روزرسانی reserved_quantity
        dessert_option.reserved_quantity += 1
        dessert_option.save()
        
        return reservation
    
    def update(self, instance, validated_data):
        """به‌روزرسانی رزرو دسر مهمان"""
        dessert_option = validated_data.get('dessert_option', instance.dessert_option)
        
        # بررسی قیمت
        if dessert_option.price <= 0:
            raise serializers.ValidationError({
                'dessert_option': 'قیمت دسر باید بیشتر از صفر باشد'
            })
        
        # اگر dessert_option تغییر کرده است
        if instance.dessert_option != dessert_option:
            # اگر رزرو فعال است، quantity قبلی را از dessert_option قبلی کم می‌کنیم
            if instance.dessert_option and instance.status == 'reserved':
                instance.dessert_option.reserved_quantity = max(0, instance.dessert_option.reserved_quantity - 1)
                instance.dessert_option.save()
            
            # quantity جدید را اضافه می‌کنیم
            if instance.status == 'reserved':
                dessert_option.reserved_quantity += 1
            dessert_option.save()
        
        # محاسبه مبلغ جدید
        validated_data['amount'] = dessert_option.price
        
        return super().update(instance, validated_data)


class SimpleGuestDessertReservationSerializer(serializers.ModelSerializer):
    """سریالایزر ساده برای رزرو دسر مهمان - فقط اطلاعات ضروری"""
    dessert_option_title = serializers.SerializerMethodField()
    guest_full_name = serializers.SerializerMethodField()
    jalali_reservation_date = serializers.SerializerMethodField()
    
    class Meta:
        model = GuestDessertReservation
        fields = [
            'id', 'guest_first_name', 'guest_last_name', 'guest_full_name',
            'dessert_option', 'dessert_option_title', 'status', 'amount', 'reservation_date', 'jalali_reservation_date'
        ]
        read_only_fields = ['reservation_date']

    @extend_schema_field(serializers.CharField())
    def get_guest_full_name(self, obj):
        return f"{obj.guest_first_name} {obj.guest_last_name}".strip()

    @extend_schema_field(serializers.CharField())
    def get_dessert_option_title(self, obj):
        if obj.dessert_option:
            return obj.dessert_option.title
        elif obj.dessert_option_info:
            return obj.dessert_option_info
        return "بدون دسر"

    @extend_schema_field(serializers.CharField())
    def get_jalali_reservation_date(self, obj):
        if obj.reservation_date:
            return datetime2jalali(obj.reservation_date).strftime('%Y/%m/%d %H:%M')
        return None

