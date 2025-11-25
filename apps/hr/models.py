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


