"""
Service for sending push notifications
"""
import json
import logging
from django.conf import settings
from pywebpush import webpush, WebPushException
from .models import PushSubscription

logger = logging.getLogger(__name__)


def send_push_notification(user, title, body, data=None, url=None):
    """
    ارسال Push Notification به کاربر
    
    Args:
        user: کاربر دریافت‌کننده
        title: عنوان نوتفیکیشن
        body: متن نوتفیکیشن
        data: داده‌های اضافی (dict)
        url: URL برای redirect (اختیاری)
    
    Returns:
        tuple: (success_count, failed_count)
    """
    subscriptions = PushSubscription.objects.filter(user=user)
    
    if not subscriptions.exists():
        logger.info(f"No push subscriptions found for user {user.username}")
        return (0, 0)
    
    webpush_settings = getattr(settings, 'WEBPUSH_SETTINGS', {})
    vapid_private_key = webpush_settings.get('VAPID_PRIVATE_KEY')
    vapid_public_key = webpush_settings.get('VAPID_PUBLIC_KEY')
    
    if not vapid_private_key or not vapid_public_key:
        logger.error("VAPID keys not configured")
        return (0, subscriptions.count())
    
    # ساخت payload
    payload = {
        'title': title,
        'body': body,
    }
    
    if data:
        payload['data'] = data
    
    if url:
        payload['url'] = url
    
    success_count = 0
    failed_count = 0
    invalid_subscriptions = []
    
    for subscription in subscriptions:
        try:
            subscription_data = {
                'endpoint': subscription.endpoint,
                'keys': subscription.keys
            }
            
            webpush(
                subscription_info=subscription_data,
                data=json.dumps(payload),
                vapid_private_key=vapid_private_key,
                vapid_claims={
                    "sub": f"mailto:{webpush_settings.get('VAPID_ADMIN_EMAIL', 'admin@example.com')}"
                }
            )
            success_count += 1
            logger.info(f"Push notification sent successfully to {user.username}")
            
        except WebPushException as e:
            failed_count += 1
            logger.error(f"Failed to send push notification to {user.username}: {str(e)}")
            
            # بررسی خطای 410 Gone یا 404 Not Found
            # این خطاها به معنای منقضی شدن یا حذف شدن subscription است
            should_remove = False
            
            # بررسی status code از response
            if hasattr(e, 'response') and e.response:
                status_code = getattr(e.response, 'status_code', None)
                if status_code in [410, 404]:
                    should_remove = True
                    logger.info(f"Subscription {subscription.id} returned {status_code} - removing")
            
            # بررسی متن خطا (برای مواردی که response در دسترس نیست)
            error_str = str(e).lower()
            if '410' in error_str or 'gone' in error_str or 'expired' in error_str or 'unsubscribed' in error_str:
                should_remove = True
                logger.info(f"Subscription {subscription.id} appears invalid based on error message - removing")
            
            if should_remove:
                invalid_subscriptions.append(subscription.id)
                logger.info(f"Marking subscription {subscription.id} for removal for user {user.username}")
        
        except Exception as e:
            failed_count += 1
            logger.error(f"Unexpected error sending push notification to {user.username}: {str(e)}")
    
    # حذف subscription های نامعتبر
    if invalid_subscriptions:
        PushSubscription.objects.filter(id__in=invalid_subscriptions).delete()
    
    return (success_count, failed_count)


def send_push_notification_to_multiple_users(users, title, body, data=None, url=None):
    """
    ارسال Push Notification به چندین کاربر
    
    Args:
        users: QuerySet یا لیست کاربران
        title: عنوان نوتفیکیشن
        body: متن نوتفیکیشن
        data: داده‌های اضافی (dict)
        url: URL برای redirect (اختیاری)
    
    Returns:
        dict: آمار ارسال {'total_users': int, 'success_count': int, 'failed_count': int}
    """
    total_users = 0
    total_success = 0
    total_failed = 0
    
    for user in users:
        success, failed = send_push_notification(user, title, body, data, url)
        total_users += 1
        total_success += success
        total_failed += failed
    
    return {
        'total_users': total_users,
        'success_count': total_success,
        'failed_count': total_failed
    }


