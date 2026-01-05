from django.contrib.auth.models import AbstractUser
from django.db import models


class Position(models.Model):
    """مدل سمت‌های سازمانی"""
    name = models.CharField(max_length=200, unique=True, verbose_name='نام سمت')
    description = models.TextField(blank=True, null=True, verbose_name='توضیحات')
    is_active = models.BooleanField(default=True, verbose_name='فعال')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='تاریخ بروزرسانی')

    class Meta:
        verbose_name = 'سمت'
        verbose_name_plural = 'سمت‌ها'
        ordering = ['name']

    def __str__(self):
        return self.name


class User(AbstractUser):
    class Role(models.TextChoices):
        EMPLOYEE = 'employee', 'Employee'
        ADMIN_FOOD = 'admin_food', 'Food Admin'
        HR = 'hr', 'Human Resources'
        SYS_ADMIN = 'sys_admin', 'System Admin'
 
    employee_number = models.CharField(max_length=20, unique=True, verbose_name='شماره پرسنلی', default='EMP001')
    first_name = models.CharField(max_length=150, verbose_name='نام')
    last_name = models.CharField(max_length=150, verbose_name='نام خانوادگی')
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.EMPLOYEE, verbose_name='نقش')
    position = models.ForeignKey('Position', on_delete=models.SET_NULL, null=True, blank=True, verbose_name='سمت', related_name='users')
    manager = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, verbose_name='مدیر', related_name='subordinates')
    centers = models.ManyToManyField('centers.Center', blank=True, verbose_name='مراکز', related_name='users')
    phone_number = models.CharField(max_length=15, verbose_name='شماره تلفن')
    national_id = models.CharField(max_length=10, blank=True, null=True, unique=True, verbose_name='کد ملی')
    profile_image = models.ImageField(upload_to='profiles/', blank=True, null=True, verbose_name='تصویر پروفایل')
    max_reservations_per_day = models.PositiveIntegerField(default=1, verbose_name='حداکثر رزرو در روز')
    max_guest_reservations_per_day = models.PositiveIntegerField(default=1, verbose_name='حداکثر رزرو مهمان در روز')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='تاریخ بروزرسانی')

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

    @property
    def center(self):
        """
        برای backward compatibility - اولین مرکز کاربر را برمی‌گرداند
        """
        centers = self.centers.all()
        return centers.first() if centers.exists() else None

    @property
    def is_admin(self):
        return self.role in [self.Role.ADMIN_FOOD, self.Role.HR, self.Role.SYS_ADMIN]

    @property
    def is_hr(self):
        return self.role == self.Role.HR

    @property
    def is_sys_admin(self):
        return self.role == self.Role.SYS_ADMIN

    def has_center(self, center):
        """
        چک می‌کند که آیا کاربر عضو مرکز مشخص شده است یا نه
        """
        if center is None:
            return False
        return self.centers.filter(id=center.id).exists()
