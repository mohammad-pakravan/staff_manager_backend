"""
Serializers for reports app
"""
from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from datetime import datetime
import jdatetime
from apps.food_management.models import FoodReport, FoodReservation


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
    center_name = serializers.SerializerMethodField()
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
    
    def get_center_name(self, obj):
        """نام مرکز از طریق daily_menu.restaurant.centers"""
        if obj.daily_menu and obj.daily_menu.restaurant and obj.daily_menu.restaurant.centers.exists():
            return ', '.join([c.name for c in obj.daily_menu.restaurant.centers.all()])
        return ''
    
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


class UserReservationsReportSerializer(serializers.Serializer):
    """سریالایزر گزارش رزروهای یک کاربر در بازه تاریخ"""
    user = serializers.DictField()
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    jalali_start_date = serializers.CharField()
    jalali_end_date = serializers.CharField()
    total_reservations = serializers.IntegerField()
    total_guest_reservations = serializers.IntegerField()
    total_dessert_reservations = serializers.IntegerField()
    total_guest_dessert_reservations = serializers.IntegerField()
    reserved_count = serializers.IntegerField()
    cancelled_count = serializers.IntegerField()
    served_count = serializers.IntegerField()
    total_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    reserved_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    reservations = serializers.ListField(child=serializers.DictField())
    guest_reservations = serializers.ListField(child=serializers.DictField())
    dessert_reservations = serializers.ListField(child=serializers.DictField())
    guest_dessert_reservations = serializers.ListField(child=serializers.DictField())