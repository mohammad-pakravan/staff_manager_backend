"""
Signals برای به‌روزرسانی تعداد رزرو شده در DailyMenuMealOption و ذخیره اطلاعات منو قبل از حذف
"""
from django.db.models.signals import post_delete, pre_delete
from django.dispatch import receiver
from .models import FoodReservation, GuestReservation, DailyMenu, DailyMenuMealOption


@receiver(post_delete, sender=FoodReservation)
def update_meal_option_on_reservation_delete(sender, instance, **kwargs):
    """به‌روزرسانی تعداد رزرو شده هنگام حذف رزرو"""
    if instance.meal_option:
        # به‌روزرسانی reserved_quantity در DailyMenuMealOption
        from django.db.models import F
        DailyMenuMealOption.objects.filter(id=instance.meal_option.id).update(
            reserved_quantity=F('reserved_quantity') - instance.quantity
        )


@receiver(post_delete, sender=GuestReservation)
def update_meal_option_on_guest_reservation_delete(sender, instance, **kwargs):
    """به‌روزرسانی تعداد رزرو شده هنگام حذف رزرو مهمان"""
    if instance.meal_option:
        # به‌روزرسانی reserved_quantity در DailyMenuMealOption
        from django.db.models import F
        DailyMenuMealOption.objects.filter(id=instance.meal_option.id).update(
            reserved_quantity=F('reserved_quantity') - 1
        )


@receiver(pre_delete, sender=DailyMenu)
def save_daily_menu_info_before_delete(sender, instance, **kwargs):
    """ذخیره اطلاعات منو در رزروها قبل از حذف"""
    center_name = instance.restaurant.center.name if instance.restaurant and instance.restaurant.center else 'بدون مرکز'
    date_str = instance.date.strftime('%Y-%m-%d')
    menu_info = f"رستوران: {instance.restaurant.name if instance.restaurant else 'بدون رستوران'} - مرکز: {center_name} - تاریخ: {date_str}"
    
    # به‌روزرسانی رزروهای غذا
    FoodReservation.objects.filter(daily_menu=instance).update(daily_menu_info=menu_info)
    
    # به‌روزرسانی رزروهای مهمان
    GuestReservation.objects.filter(daily_menu=instance).update(daily_menu_info=menu_info)


@receiver(pre_delete, sender=DailyMenuMealOption)
def save_meal_option_info_before_delete(sender, instance, **kwargs):
    """ذخیره اطلاعات غذا در رزروها قبل از حذف"""
    meal_title = instance.title
    meal_price = instance.price
    base_meal_name = instance.base_meal.title if instance.base_meal else 'نامشخص'
    meal_info = f"عنوان: {meal_title} - غذای پایه: {base_meal_name} - قیمت: {meal_price}"
    
    # به‌روزرسانی رزروهای غذا
    FoodReservation.objects.filter(meal_option=instance).update(meal_option_info=meal_info)
    
    # به‌روزرسانی رزروهای مهمان
    GuestReservation.objects.filter(meal_option=instance).update(meal_option_info=meal_info)


