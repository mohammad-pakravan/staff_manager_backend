"""
Signals برای به‌روزرسانی تعداد رزرو شده در DailyMenuMealOption و ذخیره اطلاعات منو قبل از حذف
و ارسال نوتفیکیشن هنگام تغییرات در رزروها از پنل ادمین
"""
from django.db.models.signals import post_delete, pre_delete, pre_save, post_save
from django.dispatch import receiver
from django.utils import timezone
from .models import FoodReservation, GuestReservation, DessertReservation, DailyMenu, DailyMenuMealOption, DailyMenuDessertOption
from django.db import models
from django.db import transaction
from django.db.models import F


# ذخیره وضعیت قبلی رزروها برای تشخیص تغییر
_reservation_previous_state = {}

# ذخیره وضعیت قبلی meal_option و dessert_option برای تشخیص تغییر
_meal_option_previous_state = {}
_dessert_option_previous_state = {}


def safe_decrement_reserved_quantity(meal_option_id, decrement_by):
    """
    کاهش ایمن مقدار reserved_quantity
    """
    with transaction.atomic():
        # قفل کردن ردیف برای جلوگیری از race condition
        from apps.food_management.models import DailyMenuMealOption
        meal_option = DailyMenuMealOption.objects.select_for_update().get(id=meal_option_id)
        
        # محاسبه مقدار جدید با اطمینان از عدم منفی شدن
        new_value = max(0, meal_option.reserved_quantity - decrement_by)
        
        if new_value != meal_option.reserved_quantity:
            meal_option.reserved_quantity = new_value
            meal_option.save()


@receiver(post_delete, sender=FoodReservation)
def update_meal_option_on_reservation_delete(sender, instance, **kwargs):
    """به‌روزرسانی تعداد رزرو شده هنگام حذف رزرو"""
    if instance.meal_option:
        safe_decrement_reserved_quantity(instance.meal_option.id, instance.quantity)


@receiver(post_delete, sender=GuestReservation)
def update_meal_option_on_guest_reservation_delete(sender, instance, **kwargs):
    """به‌روزرسانی تعداد رزرو شده هنگام حذف رزرو مهمان"""
    if instance.meal_option:
        safe_decrement_reserved_quantity(instance.meal_option.id, 1)
@receiver(pre_delete, sender=DailyMenu)
def save_daily_menu_info_before_delete(sender, instance, **kwargs):
    """ذخیره اطلاعات منو در رزروها قبل از حذف"""
    try:
        if instance.restaurant and instance.restaurant.centers.exists():
            center_names = ', '.join([c.name for c in instance.restaurant.centers.all()])
            center_name = center_names
        else:
            center_name = 'بدون مرکز'
    except Exception:
        center_name = 'بدون مرکز'
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


# ========== Signals برای ارسال نوتفیکیشن ==========

@receiver(pre_save, sender=FoodReservation)
def save_food_reservation_previous_state(sender, instance, **kwargs):
    """ذخیره وضعیت قبلی FoodReservation قبل از save"""
    if instance.pk:
        try:
            old_instance = FoodReservation.objects.get(pk=instance.pk)
            _reservation_previous_state[instance.pk] = {
                'status': old_instance.status,
                'meal_option_id': old_instance.meal_option.id if old_instance.meal_option else None,
                'quantity': old_instance.quantity,
            }
        except FoodReservation.DoesNotExist:
            _reservation_previous_state[instance.pk] = {
                'status': 'reserved',
                'meal_option_id': None,
                'quantity': 1,
            }
    else:
        # برای instance جدید
        _reservation_previous_state[id(instance)] = {
            'status': 'reserved',
            'meal_option_id': None,
            'quantity': 1,
        }


@receiver(post_save, sender=FoodReservation)
def send_notification_on_food_reservation_change(sender, instance, created, **kwargs):
    """ارسال نوتفیکیشن هنگام تغییر FoodReservation از پنل ادمین"""
    import logging
    logger = logging.getLogger(__name__)
    
    from apps.notifications.services import send_push_notification
    
    logger.info(f"Signal triggered for FoodReservation {instance.id if instance.pk else 'new'}, created={created}, status={instance.status}")
    
    # فقط برای رزروهای موجود (نه ایجاد جدید از ادمین)
    if created:
        # پاک کردن وضعیت قبلی
        if id(instance) in _reservation_previous_state:
            del _reservation_previous_state[id(instance)]
        logger.info("New reservation created from admin, skipping notification")
        return
    
    previous_state = _reservation_previous_state.get(instance.pk, {})
    previous_status = previous_state.get('status', 'reserved')
    previous_meal_option_id = previous_state.get('meal_option_id')
    previous_quantity = previous_state.get('quantity', 1)
    
    current_meal_option_id = instance.meal_option.id if instance.meal_option else None
    current_quantity = instance.quantity
    
    logger.info(f"Previous state: status={previous_status}, meal_option_id={previous_meal_option_id}, quantity={previous_quantity}")
    logger.info(f"Current state: status={instance.status}, meal_option_id={current_meal_option_id}, quantity={current_quantity}")
    
    should_send_notification = False
    notification_title = ''
    notification_body = ''
    
    # بررسی تغییر status به 'cancelled'
    if previous_status != 'cancelled' and instance.status == 'cancelled':
        should_send_notification = True
        # دریافت نام غذا و غذای پایه
        if instance.meal_option:
            meal_title = instance.meal_option.title
            base_meal_title = instance.meal_option.base_meal.title if instance.meal_option.base_meal else None
        elif instance.meal_option_info:
            # استخراج از meal_option_info (فرمت: "عنوان: {title} - غذای پایه: {base} - قیمت: {price}")
            parts = instance.meal_option_info.split(' - ')
            meal_title = parts[0].replace('عنوان: ', '') if parts else 'غذا'
            base_meal_title = parts[1].replace('غذای پایه: ', '') if len(parts) > 1 and 'غذای پایه:' in parts[1] else None
        else:
            meal_title = 'غذا'
            base_meal_title = None
        
        # ساخت متن کامل
        if base_meal_title:
            full_meal_name = f'{base_meal_title} ({meal_title})'
        else:
            full_meal_name = meal_title
        
        # دریافت تاریخ شمسی منو
        from jalali_date import date2jalali
        if instance.daily_menu and instance.daily_menu.date:
            jalali_date = date2jalali(instance.daily_menu.date).strftime('%Y/%m/%d')
        elif instance.daily_menu_info:
            # تلاش برای استخراج تاریخ از daily_menu_info
            try:
                date_part = instance.daily_menu_info.split('تاریخ: ')[1] if 'تاریخ: ' in instance.daily_menu_info else None
                if date_part:
                    from datetime import datetime
                    gregorian_date = datetime.strptime(date_part.strip(), '%Y-%m-%d').date()
                    jalali_date = date2jalali(gregorian_date).strftime('%Y/%m/%d')
                else:
                    jalali_date = 'نامشخص'
            except:
                jalali_date = 'نامشخص'
        else:
            jalali_date = 'نامشخص'
        
        notification_title = 'تغییر در غذای رزرو شده شما'
        notification_body = f'غذای {full_meal_name} تاریخ {jalali_date} حذف شده است.'
        logger.info(f"Status changed to cancelled, will send notification")
    
    # بررسی تغییر meal_option یا quantity (به‌روزرسانی رزرو)
    elif (previous_meal_option_id != current_meal_option_id or previous_quantity != current_quantity) and instance.status == 'reserved':
        should_send_notification = True
        # دریافت نام غذا و غذای پایه
        if instance.meal_option:
            meal_title = instance.meal_option.title
            base_meal_title = instance.meal_option.base_meal.title if instance.meal_option.base_meal else None
        elif instance.meal_option_info:
            # استخراج از meal_option_info
            parts = instance.meal_option_info.split(' - ')
            meal_title = parts[0].replace('عنوان: ', '') if parts else 'غذا'
            base_meal_title = parts[1].replace('غذای پایه: ', '') if len(parts) > 1 and 'غذای پایه:' in parts[1] else None
        else:
            meal_title = 'غذا'
            base_meal_title = None
        
        # ساخت متن کامل
        if base_meal_title:
            full_meal_name = f'{base_meal_title} ({meal_title})'
        else:
            full_meal_name = meal_title
        
        # دریافت تاریخ شمسی منو
        from jalali_date import date2jalali
        if instance.daily_menu and instance.daily_menu.date:
            jalali_date = date2jalali(instance.daily_menu.date).strftime('%Y/%m/%d')
        elif instance.daily_menu_info:
            # تلاش برای استخراج تاریخ از daily_menu_info
            try:
                date_part = instance.daily_menu_info.split('تاریخ: ')[1] if 'تاریخ: ' in instance.daily_menu_info else None
                if date_part:
                    from datetime import datetime
                    gregorian_date = datetime.strptime(date_part.strip(), '%Y-%m-%d').date()
                    jalali_date = date2jalali(gregorian_date).strftime('%Y/%m/%d')
                else:
                    jalali_date = 'نامشخص'
            except:
                jalali_date = 'نامشخص'
        else:
            jalali_date = 'نامشخص'
        
        notification_title = 'تغییر در غذای رزرو شده شما'
        notification_body = f'غذای {full_meal_name} تاریخ {jalali_date} ویرایش شده است.'
        logger.info(f"Meal option or quantity changed, will send notification")
    
    if should_send_notification:
        logger.info(f"Sending notification to user {instance.user.username}: {notification_title} - {notification_body}")
        result = send_push_notification(
            user=instance.user,
            title=notification_title,
            body=notification_body,
            data={
                'type': 'reservation_cancelled' if instance.status == 'cancelled' else 'reservation_updated',
                'reservation_id': instance.id,
            }
        )
        logger.info(f"Notification sent result: {result}")
    else:
        logger.info("No notification needed")
    
    # پاک کردن وضعیت قبلی از حافظه
    if instance.pk in _reservation_previous_state:
        del _reservation_previous_state[instance.pk]


@receiver(pre_save, sender=DessertReservation)
def save_dessert_reservation_previous_state(sender, instance, **kwargs):
    """ذخیره وضعیت قبلی DessertReservation قبل از save"""
    if instance.pk:
        try:
            old_instance = DessertReservation.objects.get(pk=instance.pk)
            _reservation_previous_state[f'dessert_{instance.pk}'] = {
                'status': old_instance.status,
                'dessert_option_id': old_instance.dessert_option.id if old_instance.dessert_option else None,
                'quantity': old_instance.quantity,
            }
        except DessertReservation.DoesNotExist:
            _reservation_previous_state[f'dessert_{instance.pk}'] = {
                'status': 'reserved',
                'dessert_option_id': None,
                'quantity': 1,
            }
    else:
        # برای instance جدید
        _reservation_previous_state[f'dessert_{id(instance)}'] = {
            'status': 'reserved',
            'dessert_option_id': None,
            'quantity': 1,
        }


@receiver(post_save, sender=DessertReservation)
def send_notification_on_dessert_reservation_change(sender, instance, created, **kwargs):
    """ارسال نوتفیکیشن هنگام تغییر DessertReservation از پنل ادمین"""
    import logging
    logger = logging.getLogger(__name__)
    
    from apps.notifications.services import send_push_notification
    
    logger.info(f"Signal triggered for DessertReservation {instance.id if instance.pk else 'new'}, created={created}, status={instance.status}")
    
    # فقط برای رزروهای موجود (نه ایجاد جدید از ادمین)
    if created:
        # پاک کردن وضعیت قبلی
        if f'dessert_{id(instance)}' in _reservation_previous_state:
            del _reservation_previous_state[f'dessert_{id(instance)}']
        logger.info("New dessert reservation created from admin, skipping notification")
        return
    
    key = f'dessert_{instance.pk}'
    previous_state = _reservation_previous_state.get(key, {})
    previous_status = previous_state.get('status', 'reserved')
    previous_dessert_option_id = previous_state.get('dessert_option_id')
    previous_quantity = previous_state.get('quantity', 1)
    
    current_dessert_option_id = instance.dessert_option.id if instance.dessert_option else None
    current_quantity = instance.quantity
    
    logger.info(f"Previous state: status={previous_status}, dessert_option_id={previous_dessert_option_id}, quantity={previous_quantity}")
    logger.info(f"Current state: status={instance.status}, dessert_option_id={current_dessert_option_id}, quantity={current_quantity}")
    
    should_send_notification = False
    notification_title = ''
    notification_body = ''
    
    # بررسی تغییر status به 'cancelled'
    if previous_status != 'cancelled' and instance.status == 'cancelled':
        should_send_notification = True
        # دریافت نام دسر و دسر پایه
        if instance.dessert_option:
            dessert_title = instance.dessert_option.title
            base_dessert_title = instance.dessert_option.base_dessert.title if instance.dessert_option.base_dessert else None
        elif instance.dessert_option_info:
            # استخراج از dessert_option_info (فرمت: "عنوان: {title} - دسر پایه: {base} - قیمت: {price}")
            parts = instance.dessert_option_info.split(' - ')
            dessert_title = parts[0].replace('عنوان: ', '') if parts else 'دسر'
            base_dessert_title = parts[1].replace('دسر پایه: ', '') if len(parts) > 1 and 'دسر پایه:' in parts[1] else None
        else:
            dessert_title = 'دسر'
            base_dessert_title = None
        
        # ساخت متن کامل
        if base_dessert_title:
            full_dessert_name = f'{base_dessert_title} ({dessert_title})'
        else:
            full_dessert_name = dessert_title
        
        # دریافت تاریخ شمسی منو
        from jalali_date import date2jalali
        if instance.daily_menu and instance.daily_menu.date:
            jalali_date = date2jalali(instance.daily_menu.date).strftime('%Y/%m/%d')
        elif instance.daily_menu_info:
            # تلاش برای استخراج تاریخ از daily_menu_info
            try:
                date_part = instance.daily_menu_info.split('تاریخ: ')[1] if 'تاریخ: ' in instance.daily_menu_info else None
                if date_part:
                    from datetime import datetime
                    gregorian_date = datetime.strptime(date_part.strip(), '%Y-%m-%d').date()
                    jalali_date = date2jalali(gregorian_date).strftime('%Y/%m/%d')
                else:
                    jalali_date = 'نامشخص'
            except:
                jalali_date = 'نامشخص'
        else:
            jalali_date = 'نامشخص'
        
        notification_title = 'تغییر در غذای رزرو شده شما'
        notification_body = f'دسر {full_dessert_name} تاریخ {jalali_date} حذف شده است.'
        logger.info(f"Status changed to cancelled, will send notification")
    
    # بررسی تغییر dessert_option یا quantity (به‌روزرسانی رزرو)
    elif (previous_dessert_option_id != current_dessert_option_id or previous_quantity != current_quantity) and instance.status == 'reserved':
        should_send_notification = True
        # دریافت نام دسر و دسر پایه
        if instance.dessert_option:
            dessert_title = instance.dessert_option.title
            base_dessert_title = instance.dessert_option.base_dessert.title if instance.dessert_option.base_dessert else None
        elif instance.dessert_option_info:
            # استخراج از dessert_option_info
            parts = instance.dessert_option_info.split(' - ')
            dessert_title = parts[0].replace('عنوان: ', '') if parts else 'دسر'
            base_dessert_title = parts[1].replace('دسر پایه: ', '') if len(parts) > 1 and 'دسر پایه:' in parts[1] else None
        else:
            dessert_title = 'دسر'
            base_dessert_title = None
        
        # ساخت متن کامل
        if base_dessert_title:
            full_dessert_name = f'{base_dessert_title} ({dessert_title})'
        else:
            full_dessert_name = dessert_title
        
        # دریافت تاریخ شمسی منو
        from jalali_date import date2jalali
        if instance.daily_menu and instance.daily_menu.date:
            jalali_date = date2jalali(instance.daily_menu.date).strftime('%Y/%m/%d')
        elif instance.daily_menu_info:
            # تلاش برای استخراج تاریخ از daily_menu_info
            try:
                date_part = instance.daily_menu_info.split('تاریخ: ')[1] if 'تاریخ: ' in instance.daily_menu_info else None
                if date_part:
                    from datetime import datetime
                    gregorian_date = datetime.strptime(date_part.strip(), '%Y-%m-%d').date()
                    jalali_date = date2jalali(gregorian_date).strftime('%Y/%m/%d')
                else:
                    jalali_date = 'نامشخص'
            except:
                jalali_date = 'نامشخص'
        else:
            jalali_date = 'نامشخص'
        
        notification_title = 'تغییر در غذای رزرو شده شما'
        notification_body = f'دسر {full_dessert_name} تاریخ {jalali_date} ویرایش شده است.'
        logger.info(f"Dessert option or quantity changed, will send notification")
    
    if should_send_notification:
        logger.info(f"Sending notification to user {instance.user.username}: {notification_title} - {notification_body}")
        result = send_push_notification(
            user=instance.user,
            title=notification_title,
            body=notification_body,
            data={
                'type': 'reservation_cancelled' if instance.status == 'cancelled' else 'reservation_updated',
                'reservation_id': instance.id,
            }
        )
        logger.info(f"Notification sent result: {result}")
    else:
        logger.info("No notification needed")
    
    # پاک کردن وضعیت قبلی از حافظه
    if key in _reservation_previous_state:
        del _reservation_previous_state[key]


# ========== Signals برای ارسال نوتفیکیشن هنگام تغییر DailyMenuMealOption ==========

@receiver(pre_save, sender=DailyMenuMealOption)
def save_meal_option_previous_state(sender, instance, **kwargs):
    """ذخیره وضعیت قبلی DailyMenuMealOption قبل از save"""
    if instance.pk:
        try:
            old_instance = DailyMenuMealOption.objects.get(pk=instance.pk)
            _meal_option_previous_state[instance.pk] = {
                'title': old_instance.title,
                'price': old_instance.price,
                'description': old_instance.description,
            }
        except DailyMenuMealOption.DoesNotExist:
            _meal_option_previous_state[instance.pk] = {
                'title': '',
                'price': 0,
                'description': '',
            }
    else:
        # برای instance جدید
        _meal_option_previous_state[id(instance)] = {
            'title': '',
            'price': 0,
            'description': '',
        }


@receiver(post_save, sender=DailyMenuMealOption)
def send_notification_on_meal_option_change(sender, instance, created, **kwargs):
    """ارسال نوتفیکیشن هنگام تغییر DailyMenuMealOption به کاربرانی که رزرو آن غذا را دارند"""
    import logging
    logger = logging.getLogger(__name__)
    
    from apps.notifications.services import send_push_notification
    
    logger.info(f"Signal triggered for DailyMenuMealOption {instance.id if instance.pk else 'new'}, created={created}")
    
    # فقط برای meal_option های موجود (نه ایجاد جدید)
    if created:
        # پاک کردن وضعیت قبلی
        if id(instance) in _meal_option_previous_state:
            del _meal_option_previous_state[id(instance)]
        logger.info("New meal option created, skipping notification")
        return
    
    previous_state = _meal_option_previous_state.get(instance.pk, {})
    previous_title = previous_state.get('title', '')
    previous_price = previous_state.get('price', 0)
    previous_description = previous_state.get('description', '')
    
    current_title = instance.title
    current_price = instance.price
    current_description = instance.description or ''
    
    logger.info(f"Previous state: title={previous_title}, price={previous_price}")
    logger.info(f"Current state: title={current_title}, price={current_price}")
    
    # بررسی تغییر title، price یا description
    if (previous_title != current_title or 
        previous_price != current_price or 
        previous_description != current_description):
        
        # دریافت همه رزروهای فعال که از این meal_option استفاده می‌کنند
        reservations = FoodReservation.objects.filter(
            meal_option=instance,
            status='reserved'
        ).select_related('user', 'daily_menu').distinct()
        
        if reservations.exists():
            # دریافت نام غذا و غذای پایه
            meal_title = instance.title
            base_meal_title = instance.base_meal.title if instance.base_meal else None
            
            # ساخت متن کامل
            if base_meal_title:
                full_meal_name = f'{base_meal_title} ({meal_title})'
            else:
                full_meal_name = meal_title
            
            # دریافت تاریخ شمسی منو
            from jalali_date import date2jalali
            if instance.daily_menu and instance.daily_menu.date:
                jalali_date = date2jalali(instance.daily_menu.date).strftime('%Y/%m/%d')
            else:
                jalali_date = 'نامشخص'
            
            notification_title = 'تغییر در غذای رزرو شده شما'
            notification_body = f'غذای {full_meal_name} تاریخ {jalali_date} ویرایش شده است.'
            
            # دریافت کاربران منحصر به فرد
            users = [reservation.user for reservation in reservations]
            unique_users = list(set(users))
            
            logger.info(f"Meal option changed, will send notification to {len(unique_users)} users")
            
            # ارسال نوتفیکیشن به هر کاربر
            for user in unique_users:
                result = send_push_notification(
                    user=user,
                    title=notification_title,
                    body=notification_body,
                    data={
                        'type': 'meal_option_updated',
                        'meal_option_id': instance.id,
                        'daily_menu_id': instance.daily_menu.id if instance.daily_menu else None,
                    }
                )
                logger.info(f"Notification sent to user {user.username}: {result}")
        else:
            logger.info("No active reservations found for this meal option")
    else:
        logger.info("No significant changes detected in meal option")
    
    # پاک کردن وضعیت قبلی از حافظه
    if instance.pk in _meal_option_previous_state:
        del _meal_option_previous_state[instance.pk]


# ========== Signals برای ارسال نوتفیکیشن هنگام تغییر DailyMenuDessertOption ==========

@receiver(pre_save, sender=DailyMenuDessertOption)
def save_dessert_option_previous_state(sender, instance, **kwargs):
    """ذخیره وضعیت قبلی DailyMenuDessertOption قبل از save"""
    if instance.pk:
        try:
            old_instance = DailyMenuDessertOption.objects.get(pk=instance.pk)
            _dessert_option_previous_state[instance.pk] = {
                'title': old_instance.title,
                'price': old_instance.price,
                'description': old_instance.description,
            }
        except DailyMenuDessertOption.DoesNotExist:
            _dessert_option_previous_state[instance.pk] = {
                'title': '',
                'price': 0,
                'description': '',
            }
    else:
        # برای instance جدید
        _dessert_option_previous_state[id(instance)] = {
            'title': '',
            'price': 0,
            'description': '',
        }


@receiver(post_save, sender=DailyMenuDessertOption)
def send_notification_on_dessert_option_change(sender, instance, created, **kwargs):
    """ارسال نوتفیکیشن هنگام تغییر DailyMenuDessertOption به کاربرانی که رزرو آن دسر را دارند"""
    import logging
    logger = logging.getLogger(__name__)
    
    from apps.notifications.services import send_push_notification
    
    logger.info(f"Signal triggered for DailyMenuDessertOption {instance.id if instance.pk else 'new'}, created={created}")
    
    # فقط برای dessert_option های موجود (نه ایجاد جدید)
    if created:
        # پاک کردن وضعیت قبلی
        if id(instance) in _dessert_option_previous_state:
            del _dessert_option_previous_state[id(instance)]
        logger.info("New dessert option created, skipping notification")
        return
    
    previous_state = _dessert_option_previous_state.get(instance.pk, {})
    previous_title = previous_state.get('title', '')
    previous_price = previous_state.get('price', 0)
    previous_description = previous_state.get('description', '')
    
    current_title = instance.title
    current_price = instance.price
    current_description = instance.description or ''
    
    logger.info(f"Previous state: title={previous_title}, price={previous_price}")
    logger.info(f"Current state: title={current_title}, price={current_price}")
    
    # بررسی تغییر title، price یا description
    if (previous_title != current_title or 
        previous_price != current_price or 
        previous_description != current_description):
        
        # دریافت همه رزروهای فعال که از این dessert_option استفاده می‌کنند
        reservations = DessertReservation.objects.filter(
            dessert_option=instance,
            status='reserved'
        ).select_related('user', 'daily_menu').distinct()
        
        if reservations.exists():
            # دریافت نام دسر و دسر پایه
            dessert_title = instance.title
            base_dessert_title = instance.base_dessert.title if instance.base_dessert else None
            
            # ساخت متن کامل
            if base_dessert_title:
                full_dessert_name = f'{base_dessert_title} ({dessert_title})'
            else:
                full_dessert_name = dessert_title
            
            # دریافت تاریخ شمسی منو
            from jalali_date import date2jalali
            if instance.daily_menu and instance.daily_menu.date:
                jalali_date = date2jalali(instance.daily_menu.date).strftime('%Y/%m/%d')
            else:
                jalali_date = 'نامشخص'
            
            notification_title = 'تغییر در غذای رزرو شده شما'
            notification_body = f'دسر {full_dessert_name} تاریخ {jalali_date} ویرایش شده است.'
            
            # دریافت کاربران منحصر به فرد
            users = [reservation.user for reservation in reservations]
            unique_users = list(set(users))
            
            logger.info(f"Dessert option changed, will send notification to {len(unique_users)} users")
            
            # ارسال نوتفیکیشن به هر کاربر
            for user in unique_users:
                result = send_push_notification(
                    user=user,
                    title=notification_title,
                    body=notification_body,
                    data={
                        'type': 'dessert_option_updated',
                        'dessert_option_id': instance.id,
                        'daily_menu_id': instance.daily_menu.id if instance.daily_menu else None,
                    }
                )
                logger.info(f"Notification sent to user {user.username}: {result}")
        else:
            logger.info("No active reservations found for this dessert option")
    else:
        logger.info("No significant changes detected in dessert option")
    
    # پاک کردن وضعیت قبلی از حافظه
    if instance.pk in _dessert_option_previous_state:
        del _dessert_option_previous_state[instance.pk]

