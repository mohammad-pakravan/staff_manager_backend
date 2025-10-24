from rest_framework import serializers
from django.utils import timezone
from drf_spectacular.utils import extend_schema_field
import jdatetime
from .models import (
    Meal, MealType, WeeklyMenu, DailyMenu, 
    FoodReservation, FoodReport, GuestReservation
)


class MealSerializer(serializers.ModelSerializer):
    center_name = serializers.CharField(source='center.name', read_only=True)
    meal_type_name = serializers.CharField(source='meal_type.name', read_only=True)
    jalali_date = serializers.SerializerMethodField()
    jalali_created_at = serializers.SerializerMethodField()
    jalali_updated_at = serializers.SerializerMethodField()
    
    class Meta:
        model = Meal
        fields = [
            'id', 'title', 'description', 'image', 'date', 'jalali_date', 'meal_type', 'meal_type_name', 
            'restaurant', 'center', 'center_name', 'is_active', 'created_at', 'jalali_created_at', 
            'updated_at', 'jalali_updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

    @extend_schema_field(serializers.CharField())
    def get_jalali_date(self, obj):
        if obj.date:
            return jdatetime.date.fromgregorian(date=obj.date).strftime('%Y/%m/%d')
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


class MealTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = MealType
        fields = [
            'id', 'name', 'start_time', 'end_time', 'is_active'
        ]


class WeeklyMenuSerializer(serializers.ModelSerializer):
    center_name = serializers.CharField(source='center.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    daily_menus_count = serializers.SerializerMethodField()
    jalali_week_start_date = serializers.SerializerMethodField()
    jalali_week_end_date = serializers.SerializerMethodField()
    jalali_created_at = serializers.SerializerMethodField()

    class Meta:
        model = WeeklyMenu
        fields = [
            'id', 'center', 'center_name', 'week_start_date', 'jalali_week_start_date',
            'week_end_date', 'jalali_week_end_date', 'is_active', 'created_by', 
            'created_by_name', 'created_at', 'jalali_created_at', 'daily_menus_count'
        ]
        read_only_fields = ['created_at']

    @extend_schema_field(serializers.IntegerField())
    def get_daily_menus_count(self, obj):
        return obj.daily_menus.count()

    @extend_schema_field(serializers.CharField())
    def get_jalali_week_start_date(self, obj):
        if obj.week_start_date:
            return jdatetime.date.fromgregorian(date=obj.week_start_date).strftime('%Y/%m/%d')
        return None

    @extend_schema_field(serializers.CharField())
    def get_jalali_week_end_date(self, obj):
        if obj.week_end_date:
            return jdatetime.date.fromgregorian(date=obj.week_end_date).strftime('%Y/%m/%d')
        return None

    @extend_schema_field(serializers.CharField())
    def get_jalali_created_at(self, obj):
        if obj.created_at:
            return jdatetime.datetime.fromgregorian(datetime=obj.created_at).strftime('%Y/%m/%d %H:%M')
        return None


class DailyMenuSerializer(serializers.ModelSerializer):
    meals = MealSerializer(many=True, read_only=True)
    meal_type = MealTypeSerializer(read_only=True)
    center_name = serializers.CharField(source='weekly_menu.center.name', read_only=True)
    meals_count = serializers.SerializerMethodField()
    jalali_date = serializers.SerializerMethodField()

    class Meta:
        model = DailyMenu
        fields = [
            'id', 'weekly_menu', 'date', 'jalali_date', 'meal_type', 'meals', 'meals_count',
            'max_reservations_per_meal', 'is_available', 'center_name'
        ]

    @extend_schema_field(serializers.IntegerField())
    def get_meals_count(self, obj):
        return obj.meals.count()

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
    class Meta:
        model = FoodReservation
        fields = ['daily_menu', 'meal', 'quantity']

    def validate(self, data):
        user = self.context['request'].user
        daily_menu = data.get('daily_menu')
        meal = data.get('meal')
        quantity = data.get('quantity', 1)
        
        # بررسی اینکه غذا در منوی روزانه موجود است
        if not daily_menu.meals.filter(id=meal.id).exists():
            raise serializers.ValidationError("این غذا در منوی روزانه موجود نیست.")
        
        # بررسی محدودیت رزرو روزانه کاربر
        if not FoodReservation.can_user_reserve(user, daily_menu, quantity):
            current_reservations = FoodReservation.get_user_daily_reservations_count(user, daily_menu)
            available_slots = user.max_reservations_per_day - current_reservations
            raise serializers.ValidationError(
                f"شما نمی‌توانید بیش از {user.max_reservations_per_day} رزرو در روز داشته باشید. "
                f"در حال حاضر {current_reservations} رزرو دارید و می‌توانید {available_slots} رزرو دیگر انجام دهید."
            )
        
        # بررسی اینکه کاربر قبلاً برای همین غذا رزرو نکرده (به جز رزرو فعلی در صورت اپدیت)
        existing_reservations = FoodReservation.objects.filter(
            user=user,
            daily_menu=daily_menu,
            meal=meal,
            status='reserved'
        )
        
        # اگر در حال اپدیت هستیم، رزرو فعلی را از بررسی مستثنی کن
        if self.instance:
            existing_reservations = existing_reservations.exclude(id=self.instance.id)
        
        if existing_reservations.exists():
            raise serializers.ValidationError("شما قبلاً برای این غذا رزرو کرده‌اید.")
        
        return data


class SimpleMealSerializer(serializers.ModelSerializer):
    """سریالایزر ساده برای غذا"""
    class Meta:
        model = Meal
        fields = ['id', 'title', 'description', 'image', 'restaurant']


class SimpleFoodReservationSerializer(serializers.ModelSerializer):
    """سریالایزر ساده برای رزرو غذا - فقط اطلاعات ضروری"""
    meal = SimpleMealSerializer(read_only=True)
    jalali_reservation_date = serializers.SerializerMethodField()
    
    class Meta:
        model = FoodReservation
        fields = [
            'id', 'meal', 'quantity', 'status', 
            'reservation_date', 'jalali_reservation_date'
        ]
        read_only_fields = ['reservation_date']

    @extend_schema_field(serializers.CharField())
    def get_jalali_reservation_date(self, obj):
        if obj.reservation_date:
            return jdatetime.datetime.fromgregorian(datetime=obj.reservation_date).strftime('%Y/%m/%d %H:%M')
        return None


class SimpleGuestReservationSerializer(serializers.ModelSerializer):
    """سریالایزر ساده برای رزرو مهمان - فقط اطلاعات ضروری"""
    meal = SimpleMealSerializer(read_only=True)
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


class WeeklyMenuCreateSerializer(serializers.ModelSerializer):
    daily_menus = serializers.ListField(
        child=serializers.DictField(),
        write_only=True,
        required=False
    )

    class Meta:
        model = WeeklyMenu
        fields = [
            'center', 'week_start_date', 'week_end_date', 'daily_menus'
        ]

    def create(self, validated_data):
        daily_menus_data = validated_data.pop('daily_menus', [])
        weekly_menu = WeeklyMenu.objects.create(**validated_data)
        
        # ایجاد منوهای روزانه
        for menu_data in daily_menus_data:
            DailyMenu.objects.create(
                weekly_menu=weekly_menu,
                **menu_data
            )
        
        return weekly_menu


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
    
    class Meta:
        model = GuestReservation
        fields = ['guest_first_name', 'guest_last_name', 'daily_menu', 'meal']

    def validate(self, data):
        user = self.context['request'].user
        daily_menu = data.get('daily_menu')
        meal = data.get('meal')
        
        # بررسی اینکه غذا در منوی روزانه موجود است
        if not daily_menu.meals.filter(id=meal.id).exists():
            raise serializers.ValidationError("این غذا در منوی روزانه موجود نیست.")
        
        # بررسی محدودیت رزرو مهمان روزانه کاربر
        if not GuestReservation.can_user_reserve_guest(user, daily_menu):
            current_guest_reservations = GuestReservation.get_user_daily_guest_reservations_count(user, daily_menu)
            available_slots = user.max_guest_reservations_per_day - current_guest_reservations
            raise serializers.ValidationError(
                f"شما نمی‌توانید بیش از {user.max_guest_reservations_per_day} رزرو مهمان در روز داشته باشید. "
                f"در حال حاضر {current_guest_reservations} رزرو مهمان دارید و می‌توانید {available_slots} رزرو مهمان دیگر انجام دهید."
            )
        
        # بررسی اینکه کاربر قبلاً برای همین مهمان و غذا رزرو نکرده (به جز رزرو فعلی در صورت اپدیت)
        existing_guest_reservations = GuestReservation.objects.filter(
            host_user=user,
            daily_menu=daily_menu,
            meal=meal,
            guest_first_name=data.get('guest_first_name'),
            guest_last_name=data.get('guest_last_name'),
            status='reserved'
        )
        
        # اگر در حال اپدیت هستیم، رزرو فعلی را از بررسی مستثنی کن
        if self.instance:
            existing_guest_reservations = existing_guest_reservations.exclude(id=self.instance.id)
        
        if existing_guest_reservations.exists():
            raise serializers.ValidationError("شما قبلاً برای این مهمان و غذا رزرو کرده‌اید.")
        
        return data

