from django.db import models
from django.utils import timezone
from apps.centers.models import Center
from apps.accounts.models import User
from apps.core.utils import to_jalali_date, get_jalali_now


class Announcement(models.Model):
    """اطلاعیه"""
    title = models.CharField(max_length=200, verbose_name='عنوان')
    lead = models.TextField(max_length=500, verbose_name='لید خبر (توضیحات کوتاه)', blank=True, null=True, help_text='توضیحات کوتاه که در ابتدای خبر نمایش داده می‌شود')
    content = models.TextField(verbose_name='متن')
    image = models.ImageField(upload_to='announcements/', blank=True, null=True, verbose_name='تصویر')
    publish_date = models.DateTimeField(verbose_name='تاریخ انتشار', default=timezone.now)
    centers = models.ManyToManyField(Center, verbose_name='مراکز', related_name='announcements')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='ایجاد شده توسط')
    is_active = models.BooleanField(default=True, verbose_name='فعال')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='تاریخ بروزرسانی')

    class Meta:
        verbose_name = 'اطلاعیه'
        verbose_name_plural = 'اطلاعیه‌ها'
        ordering = ['-publish_date']

    def __str__(self):
        return self.title

    @property
    def jalali_publish_date(self):
        """تاریخ انتشار به شمسی"""
        return to_jalali_date(self.publish_date)

    @property
    def jalali_created_at(self):
        """تاریخ ایجاد به شمسی"""
        return to_jalali_date(self.created_at)

    def save(self, *args, **kwargs):
        if not self.pk:  # اگر اطلاعیه جدید است
            self.created_by = self.created_by or User.objects.first()  # Default user
        super().save(*args, **kwargs)


