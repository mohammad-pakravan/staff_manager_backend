from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.db.models import Sum
from apps.centers.models import Center
from apps.accounts.models import User
import jdatetime


class Restaurant(models.Model):
    """مدل رستوران"""
    name = models.CharField(max_length=200, verbose_name='نام رستوران')
    address = models.TextField(blank=True, null=True, verbose_name='آدرس')
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name='تلفن')
    email = models.EmailField(blank=True, null=True, verbose_name='ایمیل')
    description = models.TextField(blank=True, null=True, verbose_name='توضیحات')
    is_active = models.BooleanField(default=True, verbose_name='فعال')
    center = models.ForeignKey(Center, on_delete=models.CASCADE, related_name='restaurants', verbose_name='مرکز')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='تاریخ بروزرسانی')

    class Meta:
        verbose_name = 'رستوران'
        verbose_name_plural = 'رستوران‌ها'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} - {self.center.name if self.center else 'بدون مرکز'}"


class BaseMeal(models.Model):
    """مدل غذای پایه"""
    title = models.CharField(max_length=200, verbose_name='عنوان')
    description = models.TextField(blank=True, null=True, verbose_name='توضیحات')
    image = models.ImageField(upload_to='meals/', blank=True, null=True, verbose_name='تصویر')
    meal_type = models.ForeignKey('MealType', on_delete=models.CASCADE, blank=True, null=True, verbose_name='وعده')
    center = models.ForeignKey(Center, on_delete=models.CASCADE, blank=True, null=True, verbose_name='مرکز')
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, blank=True, null=True, related_name='base_meals', verbose_name='رستوران')
    cancellation_deadline = models.DateTimeField(blank=True, null=True, verbose_name='مهلت لغو')
    is_active = models.BooleanField(default=True, verbose_name='فعال')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='تاریخ بروزرسانی')

    class Meta:
        verbose_name = 'غذای پایه'
        verbose_name_plural = 'غذاهای پایه'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.meal_type.name if self.meal_type else 'بدون وعده'}"


class MealOption(models.Model):
    """مدل گزینه غذا (اپشن غذا)"""
    base_meal = models.ForeignKey(BaseMeal, on_delete=models.CASCADE, related_name='options', verbose_name='گروه غذا')
    title = models.CharField(max_length=200, verbose_name='عنوان غذا')
    description = models.TextField(blank=True, null=True, verbose_name='توضیحات')
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='قیمت')
    quantity = models.PositiveIntegerField(default=0, verbose_name='تعداد')
    reserved_quantity = models.PositiveIntegerField(default=0, verbose_name='تعداد رزرو شده')
    is_active = models.BooleanField(default=True, verbose_name='فعال')
    is_default = models.BooleanField(default=False, verbose_name='گزینه پیش‌فرض')
    sort_order = models.PositiveIntegerField(default=0, verbose_name='ترتیب نمایش')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='تاریخ بروزرسانی')

    class Meta:
        verbose_name = 'غذا'
        verbose_name_plural = 'غذاها'
        ordering = ['sort_order', 'title']

    def __str__(self):
        return f"{self.base_meal.title} - {self.title}"

    @property
    def available_quantity(self):
        """تعداد موجود"""
        return max(0, self.quantity - self.reserved_quantity)

    @property
    def restaurant(self):
        """رستوران از طریق base_meal"""
        return self.base_meal.restaurant if self.base_meal else None


class Meal(models.Model):
    """مدل غذا"""
    title = models.CharField(max_length=200, verbose_name='عنوان', blank=True, null=True)
    description = models.TextField(blank=True, null=True, verbose_name='توضیحات')
    image = models.ImageField(upload_to='meals/', blank=True, null=True, verbose_name='تصویر')
    date = models.DateField(verbose_name='تاریخ', null=True, blank=True)
    meal_type = models.ForeignKey('MealType', on_delete=models.CASCADE, null=True, blank=True, verbose_name='وعده')
    restaurant = models.CharField(max_length=200, blank=True, null=True, verbose_name='رستوران')
    center = models.ForeignKey(Center, on_delete=models.CASCADE, null=True, blank=True, verbose_name='مرکز')
    is_active = models.BooleanField(default=True, verbose_name='فعال')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='تاریخ بروزرسانی')

    class Meta:
        verbose_name = 'غذا'
        verbose_name_plural = 'غذاها'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.date} - {self.meal_type.name if self.meal_type else 'بدون وعده'}"


class MealType(models.Model):
    """نوع وعده غذایی"""
    name = models.CharField(max_length=100, verbose_name='نام')
    start_time = models.TimeField(verbose_name='زمان شروع')
    end_time = models.TimeField(verbose_name='زمان پایان')
    is_active = models.BooleanField(default=True, verbose_name='فعال')

    class Meta:
        verbose_name = 'نوع وعده'
        verbose_name_plural = 'انواع وعده‌ها'
        ordering = ['start_time']

    def __str__(self):
        return self.name


class WeeklyMenu(models.Model):
    """برنامه هفتگی غذا"""
    center = models.ForeignKey(Center, on_delete=models.CASCADE, verbose_name='مرکز')
    week_start_date = models.DateField(verbose_name='تاریخ شروع هفته')
    week_end_date = models.DateField(verbose_name='تاریخ پایان هفته')
    is_active = models.BooleanField(default=True, verbose_name='فعال')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='ایجاد شده توسط')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')

    class Meta:
        verbose_name = 'برنامه هفتگی'
        verbose_name_plural = 'برنامه‌های هفتگی'
        unique_together = ['center', 'week_start_date']
        ordering = ['-week_start_date']

    def __str__(self):
        return f"{self.center.name} - {self.week_start_date} تا {self.week_end_date}"


class DailyMenu(models.Model):
    """منوی روزانه"""
    center = models.ForeignKey(Center, on_delete=models.CASCADE, verbose_name='مرکز')
    date = models.DateField(verbose_name='تاریخ')
    meal_type = models.ForeignKey(MealType, on_delete=models.CASCADE, verbose_name='وعده')
    meal_options = models.ManyToManyField(MealOption, verbose_name='غذاهای موجود', blank=True, related_name='daily_menus')
    max_reservations_per_meal = models.PositiveIntegerField(default=100, verbose_name='حداکثر رزرو برای هر غذا')
    is_available = models.BooleanField(default=True, verbose_name='در دسترس')

    class Meta:
        verbose_name = 'منوی روزانه'
        verbose_name_plural = 'منوهای روزانه'
        unique_together = ['center', 'date', 'meal_type']
        ordering = ['date', 'meal_type__start_time']

    def __str__(self):
        return f"{self.center.name if self.center else 'بدون مرکز'} - {self.date} - {self.meal_type.name if self.meal_type else 'بدون وعده'}"

    @property
    def available_spots(self):
        """تعداد جای خالی"""
        return max(0, self.max_reservations - self.current_reservations)


class FoodReservation(models.Model):
    """رزرو غذا"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='شناسه کاربر')
    daily_menu = models.ForeignKey(DailyMenu, on_delete=models.CASCADE, verbose_name='منوی روزانه', null=True, blank=True)
    meal_option = models.ForeignKey(MealOption, on_delete=models.CASCADE, verbose_name='گزینه غذا', null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1, verbose_name='تعداد رزرو')
    status = models.CharField(
        max_length=20,
        choices=[
            ('reserved', 'رزرو شده'),
            ('cancelled', 'لغو شده'),
            ('served', 'سرو شده'),
        ],
        default='reserved',
        verbose_name='وضعیت'
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='مبلغ')
    reservation_date = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ رزرو')
    cancellation_deadline = models.DateTimeField(verbose_name='مهلت لغو')
    cancelled_at = models.DateTimeField(blank=True, null=True, verbose_name='تاریخ لغو')

    class Meta:
        verbose_name = 'رزرو غذا'
        verbose_name_plural = 'رزروهای غذا'
        # unique_together = ['user', 'daily_menu', 'meal']  # موقتاً غیرفعال
        ordering = ['-reservation_date']

    def __str__(self):
        meal_title = self.meal_option.title if self.meal_option else "بدون غذا"
        return f"{self.user.username} - {meal_title} - {self.quantity} عدد"

    @classmethod
    def get_user_daily_reservations_count(cls, user, daily_menu):
        """تعداد کل رزروهای کاربر در یک منوی روزانه"""
        return cls.objects.filter(
            user=user,
            daily_menu=daily_menu,
            status='reserved'
        ).aggregate(total=models.Sum('quantity'))['total'] or 0

    @classmethod
    def get_user_date_reservations_count(cls, user, date):
        """تعداد کل رزروهای کاربر در یک تاریخ مشخص"""
        return cls.objects.filter(
            user=user,
            daily_menu__date=date,
            status='reserved'
        ).aggregate(total=models.Sum('quantity'))['total'] or 0

    @classmethod
    def can_user_reserve(cls, user, daily_menu, requested_quantity=1):
        """بررسی امکان رزرو برای کاربر"""
        current_reservations = cls.get_user_daily_reservations_count(user, daily_menu)
        return (current_reservations + requested_quantity) <= user.max_reservations_per_day

    def can_cancel(self):
        """بررسی امکان لغو رزرو"""
        if self.status != 'reserved':
            return False
        return timezone.now() < self.cancellation_deadline

    def cancel(self):
        """لغو رزرو"""
        if self.can_cancel():
            self.status = 'cancelled'
            self.cancelled_at = timezone.now()
            self.save()
            return True
        return False

    def save(self, *args, **kwargs):
        """ذخیره رزرو"""
        if not self.cancellation_deadline:
            # اگر مهلت لغو تعیین نشده، 2 ساعت قبل از وعده غذایی تنظیم کن
            if self.daily_menu and self.daily_menu.date:
                # تبدیل تاریخ میلادی به شمسی برای محاسبه
                jalali_date = jdatetime.date.fromgregorian(date=self.daily_menu.date)
                # تبدیل زمان میلادی به شمسی
                jalali_time = jdatetime.time(
                    self.daily_menu.meal_type.start_time.hour,
                    self.daily_menu.meal_type.start_time.minute,
                    self.daily_menu.meal_type.start_time.second
                )
                meal_time = jdatetime.datetime.combine(
                    jalali_date,
                    jalali_time
                )
                # تبدیل به میلادی برای ذخیره در دیتابیس
                gregorian_meal_time = meal_time.togregorian()
                self.cancellation_deadline = timezone.make_aware(gregorian_meal_time) - timezone.timedelta(hours=2)
        super().save(*args, **kwargs)


class GuestReservation(models.Model):
    """رزرو غذا برای مهمان"""
    host_user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='کاربر میزبان')
    guest_first_name = models.CharField(max_length=150, verbose_name='نام مهمان')
    guest_last_name = models.CharField(max_length=150, verbose_name='نام خانوادگی مهمان')
    daily_menu = models.ForeignKey(DailyMenu, on_delete=models.CASCADE, verbose_name='منوی روزانه', null=True, blank=True)
    meal_option = models.ForeignKey(MealOption, on_delete=models.CASCADE, verbose_name='گزینه غذا', null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ('reserved', 'رزرو شده'),
            ('cancelled', 'لغو شده'),
            ('served', 'سرو شده'),
        ],
        default='reserved',
        verbose_name='وضعیت'
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='مبلغ')
    reservation_date = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ رزرو')
    cancellation_deadline = models.DateTimeField(verbose_name='مهلت لغو')
    cancelled_at = models.DateTimeField(blank=True, null=True, verbose_name='تاریخ لغو')

    class Meta:
        verbose_name = 'رزرو مهمان'
        verbose_name_plural = 'رزروهای مهمان'
        # unique_together = ['host_user', 'daily_menu', 'meal', 'guest_first_name', 'guest_last_name']  # موقتاً غیرفعال
        ordering = ['-reservation_date']

    def __str__(self):
        meal_title = self.meal_option.title if self.meal_option else "بدون غذا"
        return f"{self.guest_first_name} {self.guest_last_name} - {meal_title} (میزبان: {self.host_user.username})"

    @classmethod
    def get_user_daily_guest_reservations_count(cls, user, daily_menu):
        """تعداد کل رزروهای مهمان کاربر در یک منوی روزانه"""
        return cls.objects.filter(
            host_user=user,
            daily_menu=daily_menu,
            status='reserved'
        ).count()

    @classmethod
    def get_user_date_guest_reservations_count(cls, user, date):
        """تعداد کل رزروهای مهمان کاربر در یک تاریخ مشخص"""
        return cls.objects.filter(
            host_user=user,
            daily_menu__date=date,
            status='reserved'
        ).count()

    @classmethod
    def can_user_reserve_guest(cls, user, daily_menu):
        """بررسی امکان رزرو مهمان برای کاربر"""
        current_guest_reservations = cls.get_user_daily_guest_reservations_count(user, daily_menu)
        return current_guest_reservations < user.max_guest_reservations_per_day

    def can_cancel(self):
        """بررسی امکان لغو رزرو"""
        return (
            self.status == 'reserved' and 
            timezone.now() < self.cancellation_deadline
        )

    def cancel(self):
        """لغو رزرو"""
        if self.can_cancel():
            self.status = 'cancelled'
            self.cancelled_at = timezone.now()
            self.save()
            return True
        return False

    def save(self, *args, **kwargs):
        if not self.pk:  # اگر رزرو جدید است
            # محاسبه مهلت لغو (2 ساعت قبل از زمان سرو غذا)
            # تبدیل تاریخ میلادی به شمسی برای محاسبه
            jalali_date = jdatetime.date.fromgregorian(date=self.daily_menu.date)
            # تبدیل زمان میلادی به شمسی
            jalali_time = jdatetime.time(
                self.daily_menu.meal_type.start_time.hour,
                self.daily_menu.meal_type.start_time.minute,
                self.daily_menu.meal_type.start_time.second
            )
            meal_time = jdatetime.datetime.combine(
                jalali_date,
                jalali_time
            )
            # تبدیل به میلادی برای ذخیره در دیتابیس
            gregorian_meal_time = meal_time.togregorian()
            self.cancellation_deadline = timezone.make_aware(gregorian_meal_time) - timezone.timedelta(hours=2)
        super().save(*args, **kwargs)


class FoodReport(models.Model):
    """گزارش غذا"""
    center = models.ForeignKey(Center, on_delete=models.CASCADE, verbose_name='مرکز')
    report_date = models.DateField(verbose_name='تاریخ گزارش')
    total_reservations = models.PositiveIntegerField(default=0, verbose_name='کل رزروها')
    total_served = models.PositiveIntegerField(default=0, verbose_name='کل سرو شده')
    total_cancelled = models.PositiveIntegerField(default=0, verbose_name='کل لغو شده')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')

    class Meta:
        verbose_name = 'گزارش غذا'
        verbose_name_plural = 'گزارش‌های غذا'
        unique_together = ['center', 'report_date']
        ordering = ['-report_date']

    def __str__(self):
        return f"{self.center.name} - {self.report_date}"
