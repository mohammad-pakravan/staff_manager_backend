"""
Signals برای ارسال نوتفیکیشن هنگام تغییرات در Announcement از پنل ادمین
"""
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from .models import Announcement


# ذخیره وضعیت قبلی is_active برای تشخیص تغییر
_announcement_previous_state = {}


@receiver(pre_save, sender=Announcement)
def save_announcement_previous_state(sender, instance, **kwargs):
    """ذخیره وضعیت قبلی is_active قبل از save"""
    if instance.pk:
        try:
            old_instance = Announcement.objects.get(pk=instance.pk)
            _announcement_previous_state[instance.pk] = {
                'is_active': old_instance.is_active,
            }
        except Announcement.DoesNotExist:
            _announcement_previous_state[instance.pk] = {
                'is_active': False,
            }
    else:
        # برای instance جدید
        _announcement_previous_state[id(instance)] = {
            'is_active': False,
        }


@receiver(post_save, sender=Announcement)
def send_notification_on_announcement_change(sender, instance, created, **kwargs):
    """ارسال نوتفیکیشن هنگام تغییر یا ایجاد Announcement"""
    import logging
    logger = logging.getLogger(__name__)
    
    from apps.notifications.services import send_push_notification_to_multiple_users
    from apps.accounts.models import User
    
    logger.info(f"Signal triggered for Announcement {instance.id}, created={created}, is_active={instance.is_active}")
    
    should_send_notification = False
    
    if created:
        # اگر اطلاعیه جدید با is_active=True ایجاد شد
        if instance.is_active:
            should_send_notification = True
            logger.info(f"New announcement created with is_active=True, will send notification")
    else:
        # اگر اطلاعیه به‌روزرسانی شد
        previous_state = _announcement_previous_state.get(instance.pk, {})
        was_active = previous_state.get('is_active', False)
        
        logger.info(f"Announcement updated: was_active={was_active}, now_active={instance.is_active}")
        
        # اگر is_active از False به True تغییر کرد
        if not was_active and instance.is_active:
            should_send_notification = True
            logger.info(f"is_active changed from False to True, will send notification")
    
    if should_send_notification:
        # دریافت کاربرانی که در مراکز مرتبط با اطلاعیه هستند
        announcement_centers = instance.centers.all()
        logger.info(f"Announcement centers count: {announcement_centers.count()}")
        
        if announcement_centers.exists():
            # اگر مراکز انتخاب شده‌اند، فقط به کاربران آن مراکز ارسال کن
            users = User.objects.filter(centers__in=announcement_centers).distinct()
            logger.info(f"Users found in selected centers: {users.count()}")
        else:
            # اگر مراکزی انتخاب نشده، به همه کاربران فعال ارسال کن
            users = User.objects.filter(is_active=True).distinct()
            logger.info(f"No centers selected, sending to all active users: {users.count()}")
        
        if users.exists():
            # استفاده از lead به عنوان body، اگر موجود نبود از title استفاده می‌کنیم
            notification_body = instance.lead if instance.lead else instance.title
            result = send_push_notification_to_multiple_users(
                users=users,
                title=instance.title,
                body=notification_body,
                data={
                    'type': 'announcement_published',
                    'announcement_id': instance.id,
                    'title': instance.title,
                },
                url=f'/announcements/{instance.id}/'
            )
            logger.info(f"Notification sent: {result}")
        else:
            logger.warning("No users found to send notification")
    
    # پاک کردن وضعیت قبلی از حافظه
    if instance.pk in _announcement_previous_state:
        del _announcement_previous_state[instance.pk]
    elif id(instance) in _announcement_previous_state:
        del _announcement_previous_state[id(instance)]

