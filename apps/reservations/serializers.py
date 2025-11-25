"""
Serializers for reservations app
"""
from rest_framework import serializers
from django.utils import timezone
from drf_spectacular.utils import extend_schema_field
from datetime import datetime
import jdatetime
from apps.food_management.models import (
    FoodReservation, GuestReservation, BaseMeal, DailyMenuMealOption,
    DessertReservation, GuestDessertReservation, Dessert
)
# Import from meals app
from apps.meals.serializers import (
    BaseMealSerializer, DailyMenuSerializer, DailyMenuMealOptionSerializer,
    BaseMealWithOptionsSerializer, SimpleMealOptionSerializer,
    DessertSerializer, SimpleDessertSerializer
)
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
            return jdatetime.datetime.fromgregorian(datetime=obj.reservation_date).strftime('%Y/%m/%d %H:%M')
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
            return jdatetime.datetime.fromgregorian(datetime=obj.reservation_date).strftime('%Y/%m/%d %H:%M')
        return None


# ========== Dessert Reservation Serializers ==========

class DessertReservationSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.username', read_only=True)
    user_full_name = serializers.SerializerMethodField()
    dessert_detail = SimpleDessertSerializer(source='dessert', read_only=True)
    daily_menu = DailyMenuSerializer(read_only=True)
    can_cancel = serializers.SerializerMethodField()
    time_until_cancellation = serializers.SerializerMethodField()
    jalali_reservation_date = serializers.SerializerMethodField()
    jalali_cancellation_deadline = serializers.SerializerMethodField()
    jalali_cancelled_at = serializers.SerializerMethodField()

    class Meta:
        model = DessertReservation
        fields = [
            'id', 'user', 'user_name', 'user_full_name', 'daily_menu', 'dessert', 'dessert_detail', 
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


class DessertReservationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = DessertReservation
        fields = ['daily_menu', 'dessert', 'quantity']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['dessert'] = serializers.PrimaryKeyRelatedField(
            queryset=Dessert.objects.all(),
            required=True
        )

    def validate(self, data):
        daily_menu = data.get('daily_menu')
        dessert = data.get('dessert')
        quantity = data.get('quantity', 1)
        
        # اگر در حال update هستیم، dessert و daily_menu را از instance بگیریم
        if self.instance:
            if 'dessert' not in data:
                dessert = self.instance.dessert
            if 'daily_menu' not in data:
                daily_menu = self.instance.daily_menu
            if 'quantity' not in data:
                quantity = self.instance.quantity
        
        if dessert and daily_menu:
            # بررسی اینکه دسر در منوی روزانه موجود است
            if not daily_menu.desserts.filter(id=dessert.id).exists():
                raise serializers.ValidationError({
                    'dessert': 'دسر باید متعلق به منوی روزانه انتخاب شده باشد'
                })
            
            # بررسی قیمت
            if dessert.price <= 0:
                raise serializers.ValidationError({
                    'dessert': 'قیمت دسر باید بیشتر از صفر باشد'
                })
            
            # بررسی موجودی
            # اگر در حال update هستیم، quantity قبلی را از reserved_quantity کم می‌کنیم
            available_quantity = dessert.available_quantity
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
        dessert = validated_data['dessert']
        quantity = validated_data.get('quantity', 1)
        
        # محدودیت رزرو برای کاربران برداشته شده است
        # کاربران می‌توانند نامحدود رزرو کنند (فقط موجودی چک می‌شود)
        
        # بررسی قیمت
        if dessert.price <= 0:
            raise serializers.ValidationError({
                'dessert': 'قیمت دسر باید بیشتر از صفر باشد'
            })
        
        # محاسبه مبلغ
        amount = dessert.price * quantity
        
        reservation = DessertReservation.objects.create(
            user=user,
            daily_menu=daily_menu,
            dessert=dessert,
            quantity=quantity,
            amount=amount
        )
        
        # به‌روزرسانی reserved_quantity
        dessert.reserved_quantity += quantity
        dessert.save()
        
        return reservation
    
    def update(self, instance, validated_data):
        """به‌روزرسانی رزرو دسر"""
        dessert = validated_data.get('dessert', instance.dessert)
        quantity = validated_data.get('quantity', instance.quantity)
        
        # بررسی قیمت
        if dessert.price <= 0:
            raise serializers.ValidationError({
                'dessert': 'قیمت دسر باید بیشتر از صفر باشد'
            })
        
        # اگر quantity یا dessert تغییر کرده است
        old_quantity = instance.quantity if instance.status == 'reserved' else 0
        new_quantity = quantity
        
        # به‌روزرسانی reserved_quantity
        if old_quantity != new_quantity or instance.dessert != dessert:
            # اگر dessert تغییر کرده، quantity قبلی را از dessert قبلی کم می‌کنیم
            if instance.dessert and instance.dessert != dessert and instance.status == 'reserved':
                instance.dessert.reserved_quantity = max(0, instance.dessert.reserved_quantity - old_quantity)
                instance.dessert.save()
            
            # quantity جدید را اضافه می‌کنیم
            if instance.status == 'reserved':
                dessert.reserved_quantity = dessert.reserved_quantity - old_quantity + new_quantity
            else:
                dessert.reserved_quantity += new_quantity
            dessert.save()
        
        # محاسبه مبلغ جدید
        validated_data['amount'] = dessert.price * quantity
        
        return super().update(instance, validated_data)


class SimpleDessertReservationSerializer(serializers.ModelSerializer):
    """سریالایزر ساده برای رزرو دسر - فقط اطلاعات ضروری"""
    dessert_title = serializers.SerializerMethodField()
    user_name = serializers.CharField(source='user.username', read_only=True)
    jalali_reservation_date = serializers.SerializerMethodField()
    
    class Meta:
        model = DessertReservation
        fields = [
            'id', 'user', 'user_name', 'dessert', 'dessert_title',
            'quantity', 'status', 'amount', 'reservation_date', 'jalali_reservation_date'
        ]
        read_only_fields = ['reservation_date']

    @extend_schema_field(serializers.CharField())
    def get_dessert_title(self, obj):
        if obj.dessert:
            return obj.dessert.title
        elif obj.dessert_info:
            return obj.dessert_info
        return "بدون دسر"

    @extend_schema_field(serializers.CharField())
    def get_jalali_reservation_date(self, obj):
        if obj.reservation_date:
            return jdatetime.datetime.fromgregorian(datetime=obj.reservation_date).strftime('%Y/%m/%d %H:%M')
        return None


class GuestDessertReservationSerializer(serializers.ModelSerializer):
    host_user_name = serializers.CharField(source='host_user.username', read_only=True)
    host_user_full_name = serializers.SerializerMethodField()
    guest_full_name = serializers.SerializerMethodField()
    dessert_detail = SimpleDessertSerializer(source='dessert', read_only=True)
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
            'daily_menu', 'dessert', 'dessert_detail', 'status', 'amount',
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


class GuestDessertReservationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = GuestDessertReservation
        fields = ['daily_menu', 'dessert', 'guest_first_name', 'guest_last_name']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['dessert'] = serializers.PrimaryKeyRelatedField(
            queryset=Dessert.objects.all(),
            required=True
        )

    def validate(self, data):
        daily_menu = data.get('daily_menu')
        dessert = data.get('dessert')
        
        # اگر در حال update هستیم، dessert و daily_menu را از instance بگیریم
        if self.instance:
            if 'dessert' not in data:
                dessert = self.instance.dessert
            if 'daily_menu' not in data:
                daily_menu = self.instance.daily_menu
        
        if dessert and daily_menu:
            # بررسی اینکه دسر در منوی روزانه موجود است
            if not daily_menu.desserts.filter(id=dessert.id).exists():
                raise serializers.ValidationError({
                    'dessert': 'دسر باید متعلق به منوی روزانه انتخاب شده باشد'
                })
            
            # بررسی قیمت
            if dessert.price <= 0:
                raise serializers.ValidationError({
                    'dessert': 'قیمت دسر باید بیشتر از صفر باشد'
                })
            
            # بررسی موجودی
            # اگر در حال update هستیم و رزرو فعال است، quantity قبلی را به موجودی اضافه می‌کنیم
            available_quantity = dessert.available_quantity
            if self.instance and self.instance.status == 'reserved':
                available_quantity += 1  # رزرو مهمان همیشه 1 است
            
            if available_quantity < 1:
                raise serializers.ValidationError({
                    'dessert': f'موجودی کافی نیست. موجودی: {available_quantity}'
                })
        
        return data

    def create(self, validated_data):
        user = self.context['request'].user
        daily_menu = validated_data['daily_menu']
        dessert = validated_data['dessert']
        
        # محدودیت رزرو برای کاربران برداشته شده است
        # کاربران می‌توانند نامحدود رزرو کنند (فقط موجودی چک می‌شود)
        
        # بررسی قیمت
        if dessert.price <= 0:
            raise serializers.ValidationError({
                'dessert': 'قیمت دسر باید بیشتر از صفر باشد'
            })
        
        # محاسبه مبلغ
        amount = dessert.price
        
        reservation = GuestDessertReservation.objects.create(
            host_user=user,
            daily_menu=daily_menu,
            dessert=dessert,
            guest_first_name=validated_data['guest_first_name'],
            guest_last_name=validated_data['guest_last_name'],
            amount=amount
        )
        
        # به‌روزرسانی reserved_quantity
        dessert.reserved_quantity += 1
        dessert.save()
        
        return reservation
    
    def update(self, instance, validated_data):
        """به‌روزرسانی رزرو دسر مهمان"""
        dessert = validated_data.get('dessert', instance.dessert)
        
        # بررسی قیمت
        if dessert.price <= 0:
            raise serializers.ValidationError({
                'dessert': 'قیمت دسر باید بیشتر از صفر باشد'
            })
        
        # اگر dessert تغییر کرده است
        if instance.dessert != dessert:
            # اگر رزرو فعال است، quantity قبلی را از dessert قبلی کم می‌کنیم
            if instance.dessert and instance.status == 'reserved':
                instance.dessert.reserved_quantity = max(0, instance.dessert.reserved_quantity - 1)
                instance.dessert.save()
            
            # quantity جدید را اضافه می‌کنیم
            if instance.status == 'reserved':
                dessert.reserved_quantity += 1
            dessert.save()
        
        # محاسبه مبلغ جدید
        validated_data['amount'] = dessert.price
        
        return super().update(instance, validated_data)


class SimpleGuestDessertReservationSerializer(serializers.ModelSerializer):
    """سریالایزر ساده برای رزرو دسر مهمان - فقط اطلاعات ضروری"""
    dessert_title = serializers.SerializerMethodField()
    guest_full_name = serializers.SerializerMethodField()
    jalali_reservation_date = serializers.SerializerMethodField()
    
    class Meta:
        model = GuestDessertReservation
        fields = [
            'id', 'guest_first_name', 'guest_last_name', 'guest_full_name',
            'dessert', 'dessert_title', 'status', 'amount', 'reservation_date', 'jalali_reservation_date'
        ]
        read_only_fields = ['reservation_date']

    @extend_schema_field(serializers.CharField())
    def get_guest_full_name(self, obj):
        return f"{obj.guest_first_name} {obj.guest_last_name}".strip()

    @extend_schema_field(serializers.CharField())
    def get_dessert_title(self, obj):
        if obj.dessert:
            return obj.dessert.title
        elif obj.dessert_info:
            return obj.dessert_info
        return "بدون دسر"

    @extend_schema_field(serializers.CharField())
    def get_jalali_reservation_date(self, obj):
        if obj.reservation_date:
            return jdatetime.datetime.fromgregorian(datetime=obj.reservation_date).strftime('%Y/%m/%d %H:%M')
        return None

