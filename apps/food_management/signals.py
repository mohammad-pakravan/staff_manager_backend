"""
Signals برای به‌روزرسانی تعداد رزرو شده در MealOption
"""
from django.db.models.signals import post_delete
from django.dispatch import receiver
from .models import FoodReservation, GuestReservation


@receiver(post_delete, sender=FoodReservation)
def update_meal_option_on_reservation_delete(sender, instance, **kwargs):
    """به‌روزرسانی تعداد رزرو شده هنگام حذف رزرو"""
    if instance.meal_option:
        instance.meal_option.update_reserved_quantity()


@receiver(post_delete, sender=GuestReservation)
def update_meal_option_on_guest_reservation_delete(sender, instance, **kwargs):
    """به‌روزرسانی تعداد رزرو شده هنگام حذف رزرو مهمان"""
    if instance.meal_option:
        instance.meal_option.update_reserved_quantity()


