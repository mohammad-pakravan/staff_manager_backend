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
    is_active = models.BooleanField(default=True, verbose_name='فعال')
    centers = models.ManyToManyField(Center, related_name='restaurants', verbose_name='مراکز')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='تاریخ بروزرسانی')

    class Meta:
        verbose_name = 'رستوران'
        verbose_name_plural = 'رستوران‌ها'
        ordering = ['name']

    def __str__(self):
        try:
            center_names = ', '.join([c.name for c in self.centers.all()])
            return f"{self.name} - {center_names if center_names else 'بدون مرکز'}"
        except Exception:
            # Fallback if database table doesn't exist yet (migration not applied)
            return f"{self.name} - بدون مرکز"


class BaseMeal(models.Model):
    """مدل غذای پایه"""
    title = models.CharField(max_length=200, verbose_name='عنوان')
    description = models.TextField(blank=True, null=True, verbose_name='توضیحات')
    ingredients = models.TextField(blank=True, null=True, verbose_name='محتویات')
    image = models.ImageField(upload_to='meals/', blank=True, null=True, verbose_name='تصویر')
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, blank=True, null=True, related_name='base_meals', verbose_name='رستوران')
    is_active = models.BooleanField(default=True, verbose_name='فعال')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='تاریخ بروزرسانی')

    class Meta:
        verbose_name = 'غذای پایه'
        verbose_name_plural = 'غذاهای پایه'
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class BaseDessert(models.Model):
    """مدل دسر پایه"""
    title = models.CharField(max_length=200, verbose_name='عنوان')
    description = models.TextField(blank=True, null=True, verbose_name='توضیحات')
    ingredients = models.TextField(blank=True, null=True, verbose_name='محتویات')
    image = models.ImageField(upload_to='desserts/', blank=True, null=True, verbose_name='تصویر')
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, blank=True, null=True, related_name='base_desserts', verbose_name='رستوران')
    is_active = models.BooleanField(default=True, verbose_name='فعال')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='تاریخ بروزرسانی')

    class Meta:
        verbose_name = 'دسر پایه'
        verbose_name_plural = 'دسرهای پایه'
        db_table = 'food_management_dessert'  # استفاده از نام جدول قدیمی برای سازگاری با migration های قبلی
        ordering = ['-created_at']

    def __str__(self):
        return self.title


# برای سازگاری با کدهای قبلی
Dessert = BaseDessert


class DailyMenu(models.Model):
    """منوی روزانه"""
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, verbose_name='رستوران')
    date = models.DateField(verbose_name='تاریخ')
    base_meals = models.ManyToManyField(BaseMeal, verbose_name='غذاهای پایه', blank=True, related_name='daily_menus')
    base_desserts = models.ManyToManyField(BaseDessert, verbose_name='دسرهای پایه', blank=True, related_name='daily_menus')
    max_reservations_per_meal = models.PositiveIntegerField(default=100, verbose_name='حداکثر رزرو برای هر غذا')
    is_available = models.BooleanField(default=True, verbose_name='در دسترس')

    class Meta:
        verbose_name = 'منوی روزانه'
        verbose_name_plural = 'منوهای روزانه'
        unique_together = ['restaurant', 'date']
        ordering = ['date']

    def __str__(self):
        return f"{self.restaurant.name if self.restaurant else 'بدون رستوران'} - {self.date}"
    
    @property
    def center(self):
        """مرکز از طریق رستوران (برای سازگاری با کدهای قبلی - اولین مرکز را برمی‌گرداند)"""
        try:
            if self.restaurant and self.restaurant.centers.exists():
                return self.restaurant.centers.first()
        except Exception:
            pass
        return None

    @property
    def available_spots(self):
        """تعداد جای خالی"""
        return max(0, self.max_reservations - self.current_reservations)
    
    @property
    def meal_options(self):
        """اپشن‌های غذا برای این منو"""
        return DailyMenuMealOption.objects.filter(daily_menu=self)
    
    @property
    def dessert_options(self):
        """اپشن‌های دسر برای این منو"""
        return DailyMenuDessertOption.objects.filter(daily_menu=self)
    
    @property
    def menu_desserts(self):
        """دسرهای این منو (برای سازگاری با کدهای قبلی)"""
        return self.dessert_options.all()


class DailyMenuMealOption(models.Model):
    """اپشن غذا برای منوی روزانه (مختص هر منو)"""
    daily_menu = models.ForeignKey(DailyMenu, on_delete=models.CASCADE, related_name='menu_meal_options', verbose_name='منوی روزانه')
    base_meal = models.ForeignKey(BaseMeal, on_delete=models.CASCADE, related_name='daily_menu_options', verbose_name='غذای پایه')
    title = models.CharField(max_length=200, verbose_name='عنوان غذا')
    description = models.TextField(blank=True, null=True, verbose_name='توضیحات')
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='قیمت')
    quantity = models.PositiveIntegerField(default=0, verbose_name='تعداد')
    reserved_quantity = models.PositiveIntegerField(default=0, verbose_name='تعداد رزرو شده')
    is_default = models.BooleanField(default=False, verbose_name='گزینه پیش‌فرض')
    cancellation_deadline = models.CharField(max_length=50, blank=True, null=True, verbose_name='مهلت لغو')
    sort_order = models.PositiveIntegerField(default=0, verbose_name='ترتیب نمایش')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='تاریخ بروزرسانی')

    class Meta:
        verbose_name = 'اپشن غذا برای منو'
        verbose_name_plural = 'اپشن‌های غذا برای منو'
        ordering = ['sort_order', 'title']
        unique_together = ['daily_menu', 'base_meal', 'title']

    def __str__(self):
        return f"{self.daily_menu} - {self.base_meal.title} - {self.title}"

    @property
    def available_quantity(self):
        """تعداد موجود"""
        return max(0, self.quantity - self.reserved_quantity)


class DailyMenuDessertOption(models.Model):
    """اپشن دسر برای منوی روزانه (مختص هر منو)"""
    daily_menu = models.ForeignKey(DailyMenu, on_delete=models.CASCADE, related_name='menu_dessert_options', verbose_name='منوی روزانه')
    base_dessert = models.ForeignKey(BaseDessert, on_delete=models.CASCADE, related_name='daily_menu_options', verbose_name='دسر پایه')
    title = models.CharField(max_length=200, verbose_name='عنوان دسر')
    description = models.TextField(blank=True, null=True, verbose_name='توضیحات')
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='قیمت')
    quantity = models.PositiveIntegerField(default=0, verbose_name='تعداد')
    reserved_quantity = models.PositiveIntegerField(default=0, verbose_name='تعداد رزرو شده')
    is_default = models.BooleanField(default=False, verbose_name='گزینه پیش‌فرض')
    cancellation_deadline = models.CharField(max_length=50, blank=True, null=True, verbose_name='مهلت لغو')
    sort_order = models.PositiveIntegerField(default=0, verbose_name='ترتیب نمایش')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='تاریخ بروزرسانی')

    class Meta:
        verbose_name = 'اپشن دسر برای منو'
        verbose_name_plural = 'اپشن‌های دسر برای منو'
        ordering = ['sort_order', 'title']
        unique_together = ['daily_menu', 'base_dessert', 'title']

    def __str__(self):
        return f"{self.daily_menu} - {self.base_dessert.title} - {self.title}"

    @property
    def available_quantity(self):
        """تعداد موجود"""
        return max(0, self.quantity - self.reserved_quantity)


class FoodReservation(models.Model):
    """رزرو غذا"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='شناسه کاربر')
    daily_menu = models.ForeignKey(DailyMenu, on_delete=models.SET_NULL, verbose_name='منوی روزانه', null=True, blank=True)
    meal_option = models.ForeignKey('DailyMenuMealOption', on_delete=models.SET_NULL, verbose_name='گزینه غذا', null=True, blank=True)
    # فیلدهای ذخیره اطلاعات منو و غذا به صورت string (برای حفظ اطلاعات بعد از حذف)
    daily_menu_info = models.TextField(blank=True, null=True, verbose_name='اطلاعات منوی روزانه (حذف شده)')
    meal_option_info = models.TextField(blank=True, null=True, verbose_name='اطلاعات غذا (حذف شده)')
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
    cancellation_deadline = models.CharField(max_length=50, blank=True, null=True, verbose_name='مهلت لغو')
    cancelled_at = models.DateTimeField(blank=True, null=True, verbose_name='تاریخ لغو')

    class Meta:
        verbose_name = 'رزرو غذا'
        verbose_name_plural = 'رزروهای غذا'
        # unique_together = ['user', 'daily_menu', 'meal']  # موقتاً غیرفعال
        ordering = ['-reservation_date']

    def __str__(self):
        if self.meal_option:
            meal_title = self.meal_option.title
        elif self.meal_option_info:
            meal_title = self.meal_option_info
        else:
            meal_title = "بدون غذا"
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
        # cancellation_deadline اکنون string است، بنابراین همیشه True برمی‌گردانیم
        # یا می‌توانید منطق مقایسه تاریخ شمسی را اضافه کنید
        return self.cancellation_deadline is not None and self.cancellation_deadline != ''

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
        # ذخیره اطلاعات منو به صورت string
        if self.daily_menu:
            try:
                if self.daily_menu.restaurant and self.daily_menu.restaurant.centers.exists():
                    center_names = ', '.join([c.name for c in self.daily_menu.restaurant.centers.all()])
                else:
                    center_names = 'بدون مرکز'
            except Exception:
                center_names = 'بدون مرکز'
            date_str = self.daily_menu.date.strftime('%Y-%m-%d')
            self.daily_menu_info = f"مرکز: {center_names} - تاریخ: {date_str}"
        elif not self.daily_menu_info and self.daily_menu is None:
            # اگر منو حذف شده و اطلاعات ذخیره نشده، اطلاعات قبلی را نگه دار
            pass
        
        # ذخیره اطلاعات غذا به صورت string
        if self.meal_option:
            meal_title = self.meal_option.title
            meal_price = self.meal_option.price if hasattr(self.meal_option, 'price') else 'نامشخص'
            base_meal_name = self.meal_option.base_meal.title if self.meal_option.base_meal else 'نامشخص'
            self.meal_option_info = f"عنوان: {meal_title} - غذای پایه: {base_meal_name} - قیمت: {meal_price}"
        elif not self.meal_option_info and self.meal_option is None:
            # اگر غذا حذف شده و اطلاعات ذخیره نشده، اطلاعات قبلی را نگه دار
            pass
        
        if not self.cancellation_deadline:
            # اگر مهلت لغو تعیین نشده، از meal_option استفاده کن
            if self.meal_option and self.meal_option.cancellation_deadline:
                self.cancellation_deadline = str(self.meal_option.cancellation_deadline)
        super().save(*args, **kwargs)


class GuestReservation(models.Model):
    """رزرو غذا برای مهمان"""
    host_user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='کاربر میزبان')
    guest_first_name = models.CharField(max_length=150, verbose_name='نام مهمان')
    guest_last_name = models.CharField(max_length=150, verbose_name='نام خانوادگی مهمان')
    daily_menu = models.ForeignKey(DailyMenu, on_delete=models.SET_NULL, verbose_name='منوی روزانه', null=True, blank=True)
    meal_option = models.ForeignKey('DailyMenuMealOption', on_delete=models.SET_NULL, verbose_name='گزینه غذا', null=True, blank=True)
    description = models.TextField(blank=True, null=True, verbose_name='توضیحات')
    # فیلدهای ذخیره اطلاعات منو و غذا به صورت string (برای حفظ اطلاعات بعد از حذف)
    daily_menu_info = models.TextField(blank=True, null=True, verbose_name='اطلاعات منوی روزانه (حذف شده)')
    meal_option_info = models.TextField(blank=True, null=True, verbose_name='اطلاعات غذا (حذف شده)')
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
    cancellation_deadline = models.CharField(max_length=50, blank=True, null=True, verbose_name='مهلت لغو')
    cancelled_at = models.DateTimeField(blank=True, null=True, verbose_name='تاریخ لغو')

    class Meta:
        verbose_name = 'رزرو مهمان'
        verbose_name_plural = 'رزروهای مهمان'
        # unique_together = ['host_user', 'daily_menu', 'meal', 'guest_first_name', 'guest_last_name']  # موقتاً غیرفعال
        ordering = ['-reservation_date']

    def __str__(self):
        if self.meal_option:
            meal_title = self.meal_option.title
        elif self.meal_option_info:
            meal_title = self.meal_option_info
        else:
            meal_title = "بدون غذا"
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
        # cancellation_deadline اکنون string است، بنابراین بررسی می‌کنیم که وجود داشته باشد
        return (
            self.status == 'reserved' and 
            self.cancellation_deadline is not None and 
            self.cancellation_deadline != ''
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
        # ذخیره اطلاعات منو به صورت string
        if self.daily_menu:
            try:
                if self.daily_menu.restaurant and self.daily_menu.restaurant.centers.exists():
                    center_names = ', '.join([c.name for c in self.daily_menu.restaurant.centers.all()])
                else:
                    center_names = 'بدون مرکز'
            except Exception:
                center_names = 'بدون مرکز'
            date_str = self.daily_menu.date.strftime('%Y-%m-%d')
            self.daily_menu_info = f"مرکز: {center_names} - تاریخ: {date_str}"
        elif not self.daily_menu_info and self.daily_menu is None:
            # اگر منو حذف شده و اطلاعات ذخیره نشده، اطلاعات قبلی را نگه دار
            pass
        
        # ذخیره اطلاعات غذا به صورت string
        if self.meal_option:
            meal_title = self.meal_option.title
            meal_price = self.meal_option.price if hasattr(self.meal_option, 'price') else 'نامشخص'
            base_meal_name = self.meal_option.base_meal.title if self.meal_option.base_meal else 'نامشخص'
            self.meal_option_info = f"عنوان: {meal_title} - غذای پایه: {base_meal_name} - قیمت: {meal_price}"
        elif not self.meal_option_info and self.meal_option is None:
            # اگر غذا حذف شده و اطلاعات ذخیره نشده، اطلاعات قبلی را نگه دار
            pass
        
        if not self.pk:  # اگر رزرو جدید است
            # محاسبه مهلت لغو
            if not self.cancellation_deadline:
                # اگر مهلت لغو تعیین نشده، از meal_option استفاده کن
                if self.meal_option and self.meal_option.cancellation_deadline:
                    self.cancellation_deadline = str(self.meal_option.cancellation_deadline)
        super().save(*args, **kwargs)


class DessertReservation(models.Model):
    """رزرو دسر"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='شناسه کاربر')
    daily_menu = models.ForeignKey(DailyMenu, on_delete=models.SET_NULL, verbose_name='منوی روزانه', null=True, blank=True)
    dessert_option = models.ForeignKey('DailyMenuDessertOption', on_delete=models.SET_NULL, verbose_name='گزینه دسر', null=True, blank=True)
    # فیلدهای ذخیره اطلاعات منو و دسر به صورت string (برای حفظ اطلاعات بعد از حذف)
    daily_menu_info = models.TextField(blank=True, null=True, verbose_name='اطلاعات منوی روزانه (حذف شده)')
    dessert_option_info = models.TextField(blank=True, null=True, verbose_name='اطلاعات دسر (حذف شده)')
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
    cancellation_deadline = models.CharField(max_length=50, blank=True, null=True, verbose_name='مهلت لغو')
    cancelled_at = models.DateTimeField(blank=True, null=True, verbose_name='تاریخ لغو')

    class Meta:
        verbose_name = 'رزرو دسر'
        verbose_name_plural = 'رزروهای دسر'
        ordering = ['-reservation_date']

    def __str__(self):
        if self.dessert_option:
            dessert_title = self.dessert_option.title
        elif self.dessert_option_info:
            dessert_title = self.dessert_option_info
        else:
            dessert_title = "بدون دسر"
        return f"{self.user.username} - {dessert_title} - {self.quantity} عدد"

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
        # cancellation_deadline اکنون string است، بنابراین همیشه True برمی‌گردانیم
        # یا می‌توانید منطق مقایسه تاریخ شمسی را اضافه کنید
        return self.cancellation_deadline is not None and self.cancellation_deadline != ''

    def cancel(self):
        """لغو رزرو"""
        if self.can_cancel():
            # کاهش reserved_quantity
            if self.dessert_option and self.status == 'reserved':
                self.dessert_option.reserved_quantity = max(0, self.dessert_option.reserved_quantity - self.quantity)
                self.dessert_option.save()
            
            self.status = 'cancelled'
            self.cancelled_at = timezone.now()
            self.save()
            return True
        return False

    def save(self, *args, **kwargs):
        """ذخیره رزرو"""
        # ذخیره اطلاعات منو به صورت string
        if self.daily_menu:
            try:
                if self.daily_menu.restaurant and self.daily_menu.restaurant.centers.exists():
                    center_names = ', '.join([c.name for c in self.daily_menu.restaurant.centers.all()])
                else:
                    center_names = 'بدون مرکز'
            except Exception:
                center_names = 'بدون مرکز'
            date_str = self.daily_menu.date.strftime('%Y-%m-%d')
            self.daily_menu_info = f"مرکز: {center_names} - تاریخ: {date_str}"
        elif not self.daily_menu_info and self.daily_menu is None:
            pass
        
        # ذخیره اطلاعات دسر به صورت string
        if self.dessert_option:
            dessert_title = self.dessert_option.title
            dessert_price = self.dessert_option.price if hasattr(self.dessert_option, 'price') else 'نامشخص'
            base_dessert_name = self.dessert_option.base_dessert.title if self.dessert_option.base_dessert else 'نامشخص'
            self.dessert_option_info = f"عنوان: {dessert_title} - دسر پایه: {base_dessert_name} - قیمت: {dessert_price}"
        elif not self.dessert_option_info and self.dessert_option is None:
            pass
        
        if not self.cancellation_deadline:
            # اگر مهلت لغو تعیین نشده، از dessert_option استفاده کن
            if self.dessert_option and self.dessert_option.cancellation_deadline:
                self.cancellation_deadline = str(self.dessert_option.cancellation_deadline)
        super().save(*args, **kwargs)


class GuestDessertReservation(models.Model):
    """رزرو دسر برای مهمان"""
    host_user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='کاربر میزبان')
    guest_first_name = models.CharField(max_length=150, verbose_name='نام مهمان')
    guest_last_name = models.CharField(max_length=150, verbose_name='نام خانوادگی مهمان')
    daily_menu = models.ForeignKey(DailyMenu, on_delete=models.SET_NULL, verbose_name='منوی روزانه', null=True, blank=True)
    dessert_option = models.ForeignKey('DailyMenuDessertOption', on_delete=models.SET_NULL, verbose_name='گزینه دسر', null=True, blank=True)
    # فیلدهای ذخیره اطلاعات منو و دسر به صورت string (برای حفظ اطلاعات بعد از حذف)
    daily_menu_info = models.TextField(blank=True, null=True, verbose_name='اطلاعات منوی روزانه (حذف شده)')
    dessert_option_info = models.TextField(blank=True, null=True, verbose_name='اطلاعات دسر (حذف شده)')
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
    cancellation_deadline = models.CharField(max_length=50, blank=True, null=True, verbose_name='مهلت لغو')
    cancelled_at = models.DateTimeField(blank=True, null=True, verbose_name='تاریخ لغو')

    class Meta:
        verbose_name = 'رزرو دسر مهمان'
        verbose_name_plural = 'رزروهای دسر مهمان'
        ordering = ['-reservation_date']

    def __str__(self):
        if self.dessert_option:
            dessert_title = self.dessert_option.title
        elif self.dessert_option_info:
            dessert_title = self.dessert_option_info
        else:
            dessert_title = "بدون دسر"
        return f"{self.guest_first_name} {self.guest_last_name} - {dessert_title} (میزبان: {self.host_user.username})"

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
        # cancellation_deadline اکنون string است، بنابراین بررسی می‌کنیم که وجود داشته باشد
        return (
            self.status == 'reserved' and 
            self.cancellation_deadline is not None and 
            self.cancellation_deadline != ''
        )

    def cancel(self):
        """لغو رزرو"""
        if self.can_cancel():
            # کاهش reserved_quantity
            if self.dessert_option and self.status == 'reserved':
                self.dessert_option.reserved_quantity = max(0, self.dessert_option.reserved_quantity - 1)
                self.dessert_option.save()
            
            self.status = 'cancelled'
            self.cancelled_at = timezone.now()
            self.save()
            return True
        return False

    def save(self, *args, **kwargs):
        # ذخیره اطلاعات منو به صورت string
        if self.daily_menu:
            try:
                if self.daily_menu.restaurant and self.daily_menu.restaurant.centers.exists():
                    center_names = ', '.join([c.name for c in self.daily_menu.restaurant.centers.all()])
                else:
                    center_names = 'بدون مرکز'
            except Exception:
                center_names = 'بدون مرکز'
            date_str = self.daily_menu.date.strftime('%Y-%m-%d')
            self.daily_menu_info = f"مرکز: {center_names} - تاریخ: {date_str}"
        elif not self.daily_menu_info and self.daily_menu is None:
            pass
        
        # ذخیره اطلاعات دسر به صورت string
        if self.dessert_option:
            dessert_title = self.dessert_option.title
            dessert_price = self.dessert_option.price if hasattr(self.dessert_option, 'price') else 'نامشخص'
            base_dessert_name = self.dessert_option.base_dessert.title if self.dessert_option.base_dessert else 'نامشخص'
            self.dessert_option_info = f"عنوان: {dessert_title} - دسر پایه: {base_dessert_name} - قیمت: {dessert_price}"
        elif not self.dessert_option_info and self.dessert_option is None:
            pass
        
        if not self.pk:  # اگر رزرو جدید است
            # محاسبه مهلت لغو
            if not self.cancellation_deadline:
                # اگر مهلت لغو تعیین نشده، از dessert_option استفاده کن
                if self.dessert_option and self.dessert_option.cancellation_deadline:
                    self.cancellation_deadline = str(self.dessert_option.cancellation_deadline)
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
