"""
Models for notifications app
"""
from django.db import models
from django.conf import settings


class PushSubscription(models.Model):
    """مدل ذخیره subscription های Push Notification کاربران"""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='push_subscriptions',
        verbose_name='کاربر'
    )
    endpoint = models.URLField(max_length=500, verbose_name='Endpoint')
    keys = models.JSONField(verbose_name='کلیدهای رمزنگاری')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='تاریخ بروزرسانی')

    class Meta:
        verbose_name = 'اشتراک Push Notification'
        verbose_name_plural = 'اشتراک‌های Push Notification'
        unique_together = ['user', 'endpoint']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.endpoint[:50]}..."


