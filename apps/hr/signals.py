"""
Signals برای ارسال نوتفیکیشن هنگام تغییرات در Announcement از پنل ادمین
"""
from django.db.models.signals import pre_save, post_save, m2m_changed
from django.dispatch import receiver
from .models import Announcement


# ذخیره وضعیت قبلی is_active برای تشخیص تغییر
_announcement_previous_state = {}

# برای جلوگیری از ارسال تکراری نوتیفیکیشن
_notification_sent_for_announcement = set()


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
    from django.db import transaction
    
    logger = logging.getLogger(__name__)
    
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
    
    # اگر باید نوتیفیکیشن ارسال شود، از transaction.on_commit استفاده می‌کنیم
    # تا مطمئن شویم که روابط ManyToMany ذخیره شده‌اند
    if should_send_notification and instance.is_announcement:
        def send_notification_after_commit():
            from apps.notifications.services import send_push_notification_to_multiple_users
            from apps.accounts.models import User
            
            # بارگذاری مجدد instance برای اطمینان از داشتن روابط ManyToMany
            try:
                announcement = Announcement.objects.prefetch_related('centers', 'target_users').get(pk=instance.pk)
            except Announcement.DoesNotExist:
                logger.warning(f"Announcement {instance.pk} not found after commit")
                return
            
            # جمع‌آوری کاربران: از مراکز، کاربران خاص، یا همه کاربران
            users = User.objects.none()
            
            # اگر send_to_all_users فعال باشد، به همه کاربران ارسال کن
            if announcement.send_to_all_users:
                users = User.objects.all()
                logger.info(f"send_to_all_users is True, sending to all users: {users.count()}")
            else:
                # کاربران مراکز انتخاب شده
                announcement_centers = announcement.centers.all()
                logger.info(f"Announcement centers count: {announcement_centers.count()}")
                if announcement_centers.exists():
                    center_users = User.objects.filter(centers__in=announcement_centers).distinct()
                    users = users.union(center_users)
                    logger.info(f"Users found in selected centers: {center_users.count()}")
                
                # کاربران خاص انتخاب شده
                target_users = announcement.target_users.all()
                logger.info(f"Target users count: {target_users.count()}")
                if target_users.exists():
                    users = users.union(target_users)
                    logger.info(f"Target users added: {target_users.count()}")
            
            if users.exists():
                # استفاده از lead به عنوان body، اگر موجود نبود از title استفاده می‌کنیم
                notification_body = announcement.lead if announcement.lead else announcement.title
                # تبدیل به list برای distinct کردن و شمارش
                user_ids = list(set(users.values_list('id', flat=True)))
                user_count = len(user_ids)
                final_users = User.objects.filter(id__in=user_ids)
                
                result = send_push_notification_to_multiple_users(
                    users=final_users,
                    title=announcement.title,
                    body=notification_body,
                    data={
                        'type': 'announcement_published',
                        'announcement_id': announcement.id,
                        'title': announcement.title,
                    },
                    url=f'/announcements/{announcement.id}/'
                )
                logger.info(f"Notification sent to {user_count} users: {result}")
            else:
                logger.warning("No users found to send notification")
        
        # استفاده از on_commit برای اطمینان از ذخیره شدن روابط ManyToMany
        transaction.on_commit(send_notification_after_commit)
    
    # پاک کردن وضعیت قبلی از حافظه
    if instance.pk in _announcement_previous_state:
        del _announcement_previous_state[instance.pk]
    elif id(instance) in _announcement_previous_state:
        del _announcement_previous_state[id(instance)]


@receiver(m2m_changed, sender=Announcement.centers.through)
@receiver(m2m_changed, sender=Announcement.target_users.through)
def send_notification_on_m2m_change(sender, instance, action, pk_set, **kwargs):
    """ارسال نوتفیکیشن هنگام تغییر روابط ManyToMany (centers یا target_users)"""
    # فقط وقتی که روابط اضافه می‌شوند (post_add) و اطلاعیه فعال است
    if action == 'post_add' and instance.pk and instance.is_active and instance.is_announcement:
        import logging
        from django.db import transaction
        
        logger = logging.getLogger(__name__)
        
        logger.info(f"m2m_changed signal triggered for Announcement {instance.id}, action={action}")
        
        # استفاده از on_commit برای اطمینان از ذخیره شدن کامل روابط
        def send_notification_after_m2m_commit():
            # بررسی اینکه آیا قبلاً نوتیفیکیشن ارسال شده است
            notification_key = f"announcement_{instance.pk}_m2m"
            if notification_key in _notification_sent_for_announcement:
                logger.info(f"Notification already sent for announcement {instance.pk} via m2m_changed")
                return
            
            from apps.notifications.services import send_push_notification_to_multiple_users
            from apps.accounts.models import User
            
            # بارگذاری مجدد instance برای اطمینان از داشتن روابط ManyToMany
            try:
                announcement = Announcement.objects.prefetch_related('centers', 'target_users').get(pk=instance.pk)
            except Announcement.DoesNotExist:
                logger.warning(f"Announcement {instance.pk} not found after m2m commit")
                return
            
            # جمع‌آوری کاربران: از مراکز، کاربران خاص، یا همه کاربران
            users = User.objects.none()
            
            # اگر send_to_all_users فعال باشد، به همه کاربران ارسال کن
            if announcement.send_to_all_users:
                users = User.objects.all()
                logger.info(f"send_to_all_users is True, sending to all users: {users.count()}")
            else:
                # کاربران مراکز انتخاب شده
                announcement_centers = announcement.centers.all()
                logger.info(f"Announcement centers count: {announcement_centers.count()}")
                if announcement_centers.exists():
                    center_users = User.objects.filter(centers__in=announcement_centers).distinct()
                    users = users.union(center_users)
                    logger.info(f"Users found in selected centers: {center_users.count()}")
                
                # کاربران خاص انتخاب شده
                target_users = announcement.target_users.all()
                logger.info(f"Target users count: {target_users.count()}")
                if target_users.exists():
                    users = users.union(target_users)
                    logger.info(f"Target users added: {target_users.count()}")
            
            if users.exists():
                # استفاده از lead به عنوان body، اگر موجود نبود از title استفاده می‌کنیم
                notification_body = announcement.lead if announcement.lead else announcement.title
                # تبدیل به list برای distinct کردن و شمارش
                user_ids = list(set(users.values_list('id', flat=True)))
                user_count = len(user_ids)
                final_users = User.objects.filter(id__in=user_ids)
                
                result = send_push_notification_to_multiple_users(
                    users=final_users,
                    title=announcement.title,
                    body=notification_body,
                    data={
                        'type': 'announcement_published',
                        'announcement_id': announcement.id,
                        'title': announcement.title,
                    },
                    url=f'/announcements/{announcement.id}/'
                )
                logger.info(f"Notification sent to {user_count} users: {result}")
                # علامت‌گذاری برای جلوگیری از ارسال تکراری
                _notification_sent_for_announcement.add(notification_key)
            else:
                logger.warning("No users found to send notification")
        
        transaction.on_commit(send_notification_after_m2m_commit)

