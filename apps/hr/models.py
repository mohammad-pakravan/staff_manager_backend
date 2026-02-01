from django.db import models
from django.utils import timezone
from apps.centers.models import Center
from apps.accounts.models import User
from apps.core.utils import to_jalali_date, get_jalali_now
import logging

logger = logging.getLogger(__name__)


class Announcement(models.Model):
    """اطلاعیه و خبر"""
    title = models.CharField(max_length=200, verbose_name='عنوان')
    lead = models.TextField(max_length=500, verbose_name='لید خبر (توضیحات کوتاه)', blank=True, null=True, help_text='توضیحات کوتاه که در ابتدای خبر نمایش داده می‌شود')
    content = models.TextField(verbose_name='متن')
    image = models.ImageField(upload_to='announcements/', blank=True, null=True, verbose_name='تصویر')
    publish_date = models.DateTimeField(verbose_name='تاریخ انتشار', default=timezone.now)
    centers = models.ManyToManyField(Center, verbose_name='مراکز', related_name='announcements', blank=True, help_text='برای خبر و اطلاعیه: انتخاب یک یا چند مرکز')
    send_to_all_users = models.BooleanField(default=False, verbose_name='ارسال به کل کاربران', help_text='فقط برای اطلاعیه: اگر فعال باشد، به همه کاربران ارسال می‌شود')
    target_users = models.ManyToManyField(User, verbose_name='کاربران خاص', related_name='targeted_announcements', blank=True, help_text='فقط برای اطلاعیه: انتخاب یک یا چند کاربر خاص (در صورت عدم انتخاب send_to_all_users)')
    is_announcement = models.BooleanField(default=False, verbose_name='به عنوان اطلاعیه منتشر شود')
    is_news = models.BooleanField(default=False, verbose_name='به عنوان خبر منتشر شود')
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
    
    def clean(self):
        """اعتبارسنجی: حداقل یکی از is_announcement یا is_news باید True باشد"""
        from django.core.exceptions import ValidationError
        if not self.is_announcement and not self.is_news:
            raise ValidationError('حداقل یکی از "به عنوان اطلاعیه منتشر شود" یا "به عنوان خبر منتشر شود" باید انتخاب شود.')


class AnnouncementReadStatus(models.Model):
    """وضعیت خوانده شده/نشده اطلاعیه‌ها و خبرها برای هر کاربر"""
    announcement = models.ForeignKey(Announcement, on_delete=models.CASCADE, verbose_name='اطلاعیه/خبر', related_name='read_statuses')
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='کاربر', related_name='announcement_read_statuses')
    read_at = models.DateTimeField(blank=True, null=True, verbose_name='تاریخ خوانده شدن')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    
    class Meta:
        verbose_name = 'وضعیت خوانده شده اطلاعیه'
        verbose_name_plural = 'وضعیت‌های خوانده شده اطلاعیه‌ها'
        unique_together = ['announcement', 'user']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.announcement.title[:50]}"
    
    @property
    def is_read(self):
        """بررسی اینکه آیا خوانده شده است یا نه"""
        return self.read_at is not None
    
    def mark_as_read(self):
        """علامت‌گذاری به عنوان خوانده شده"""
        if not self.read_at:
            self.read_at = timezone.now()
            self.save(update_fields=['read_at'])


class Feedback(models.Model):
    """نظرات کاربران"""
    class Status(models.TextChoices):
        UNREAD = 'unread', 'خوانده نشده'
        READ = 'read', 'خوانده شده'
        REPLIED = 'replied', 'پاسخ داده شده'
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='کاربر', related_name='feedbacks')
    message = models.TextField(verbose_name='متن نظر')
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.UNREAD,
        verbose_name='وضعیت'
    )
    read_at = models.DateTimeField(blank=True, null=True, verbose_name='تاریخ خوانده شدن')
    read_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name='خوانده شده توسط',
        related_name='read_feedbacks'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='تاریخ بروزرسانی')

    class Meta:
        verbose_name = 'نظر'
        verbose_name_plural = 'نظرات'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.message[:50]}"

    @property
    def jalali_created_at(self):
        """تاریخ ایجاد به شمسی"""
        return to_jalali_date(self.created_at)

    @property
    def jalali_read_at(self):
        """تاریخ خوانده شدن به شمسی"""
        if self.read_at:
            return to_jalali_date(self.read_at)
        return None

    def mark_as_read(self, read_by_user):
        """علامت‌گذاری به عنوان خوانده شده"""
        if self.status == self.Status.UNREAD:
            self.status = self.Status.READ
            self.read_at = timezone.now()
            self.read_by = read_by_user
            self.save()


class InsuranceForm(models.Model):
    """فرم بیمه"""
    class Status(models.TextChoices):
        PENDING = 'pending', 'در انتظار'
        APPROVED = 'approved', 'تایید شده'
        REJECTED = 'rejected', 'رد شده'
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='کاربر', related_name='insurance_forms')
    file = models.FileField(upload_to='insurance_forms/', verbose_name='فایل بیمه')
    description = models.TextField(blank=True, null=True, verbose_name='توضیحات')
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        verbose_name='وضعیت'
    )
    reviewed_at = models.DateTimeField(blank=True, null=True, verbose_name='تاریخ بررسی')
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name='بررسی شده توسط',
        related_name='reviewed_insurance_forms'
    )
    review_comment = models.TextField(blank=True, null=True, verbose_name='نظر بررسی‌کننده')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='تاریخ بروزرسانی')

    class Meta:
        verbose_name = 'فرم بیمه'
        verbose_name_plural = 'فرم‌های بیمه'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.get_status_display()}"

    @property
    def jalali_created_at(self):
        """تاریخ ایجاد به شمسی"""
        return to_jalali_date(self.created_at)

    @property
    def jalali_reviewed_at(self):
        """تاریخ بررسی به شمسی"""
        if self.reviewed_at:
            return to_jalali_date(self.reviewed_at)
        return None

    def review(self, reviewed_by_user, status, comment=''):
        """بررسی فرم بیمه"""
        self.status = status
        self.reviewed_at = timezone.now()
        self.reviewed_by = reviewed_by_user
        self.review_comment = comment
        self.save()


class PhoneBook(models.Model):
    """دفترچه تلفن"""
    title = models.CharField(max_length=200, verbose_name='عنوان')
    phone = models.CharField(max_length=20, verbose_name='شماره تلفن')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='تاریخ بروزرسانی')

    class Meta:
        verbose_name = 'دفترچه تلفن'
        verbose_name_plural = 'دفترچه تلفن'
        ordering = ['title']

    def __str__(self):
        return f"{self.title} - {self.phone}"

    @property
    def jalali_created_at(self):
        """تاریخ ایجاد به شمسی"""
        return to_jalali_date(self.created_at)


class Story(models.Model):
    """استوری"""
    text = models.TextField(verbose_name='متن', blank=True, null=True)
    thumbnail_image = models.ImageField(upload_to='stories/', verbose_name='تصویر شاخص', blank=True, null=True)
    content_file = models.FileField(
        upload_to='stories/content/',
        verbose_name='محتوای قابل نمایش (عکس یا ویدیو)',
        help_text='می‌تواند عکس یا ویدیو باشد',
        blank=True,
        null=True
    )
   
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='ایجاد شده توسط', related_name='created_stories')
    is_active = models.BooleanField(default=True, verbose_name='فعال')
    expiry_date = models.DateTimeField(
        blank=True, 
        null=True, 
        verbose_name='تاریخ انقضا',
        help_text='بعد از این تاریخ فایل‌های استوری به صورت خودکار پاک می‌شوند'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='تاریخ بروزرسانی')

    class Meta:
        verbose_name = 'استوری'
        verbose_name_plural = 'استوری‌ها'
        ordering = ['-created_at']

    def __str__(self):
        return f"استوری - {self.created_by.username if self.created_by else 'بدون کاربر'}"
    
    @property
    def jalali_created_at(self):
        """تاریخ ایجاد به شمسی"""
        return to_jalali_date(self.created_at)
    
    @property
    def is_expired(self):
        """بررسی منقضی شدن استوری"""
        if self.expiry_date:
            return timezone.now() > self.expiry_date
        return False
    
    @property
    def content_type(self):
        """نوع محتوا (image یا video)"""
        if not self.content_file:
            return None
        
        content_type = self.content_file.name.lower()
        if content_type.endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp')):
            return 'image'
        elif content_type.endswith(('.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm', '.mkv')):
            return 'video'
        return 'unknown'
    
    def delete_files(self):
        """پاک کردن فایل‌های استوری از هارد دیسک و خالی کردن فیلدها"""
        import os
        from django.conf import settings
        
        # پاک کردن thumbnail_image
        if self.thumbnail_image:
            file_path = os.path.join(settings.MEDIA_ROOT, self.thumbnail_image.name)
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    logger.info(f"Deleted thumbnail file: {file_path}")
                except Exception as e:
                    logger.error(f"Error deleting thumbnail for story {self.id}: {e}")
            # خالی کردن فیلد (record باقی می‌ماند)
            self.thumbnail_image = None
        
        # پاک کردن content_file
        if self.content_file:
            file_path = os.path.join(settings.MEDIA_ROOT, self.content_file.name)
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    logger.info(f"Deleted content file: {file_path}")
                except Exception as e:
                    logger.error(f"Error deleting content file for story {self.id}: {e}")
            # خالی کردن فیلد (record باقی می‌ماند)
            self.content_file = None
        
        # ذخیره تغییرات (بدون حذف record)
        self.save(update_fields=['thumbnail_image', 'content_file'])



class FirstPageImage(models.Model):
    name = models.CharField(max_length=200, verbose_name='عنوان')
    image = models.ImageField(upload_to="first-page-image")

    class Meta:
        verbose_name = ("firstpageimage")
        verbose_name_plural = ("firstpageimages")

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # keep only one object in table
        if not self.pk and FirstPageImage.objects.exists():
            FirstPageImage.objects.all().delete()
        super().save(*args, **kwargs)
