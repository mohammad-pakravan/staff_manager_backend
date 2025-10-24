from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        EMPLOYEE = 'employee', 'Employee'
        ADMIN_FOOD = 'admin_food', 'Food Admin'
        HR = 'hr', 'Human Resources'
        SYS_ADMIN = 'sys_admin', 'System Admin'

    # فیلدهای جدید بر اساس ساختار اطلاعاتی
    employee_number = models.CharField(max_length=20, unique=True, verbose_name='شماره پرسنلی', default='EMP001')
    first_name = models.CharField(max_length=150, verbose_name='نام')
    last_name = models.CharField(max_length=150, verbose_name='نام خانوادگی')
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.EMPLOYEE, verbose_name='نقش')
    center = models.ForeignKey('centers.Center', on_delete=models.SET_NULL, null=True, blank=True, verbose_name='مرکز')
    phone_number = models.CharField(max_length=15, blank=True, null=True, verbose_name='شماره تلفن')
    max_reservations_per_day = models.PositiveIntegerField(default=1, verbose_name='حداکثر رزرو در روز')
    max_guest_reservations_per_day = models.PositiveIntegerField(default=1, verbose_name='حداکثر رزرو مهمان در روز')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='تاریخ بروزرسانی')

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

    @property
    def is_admin(self):
        return self.role in [self.Role.ADMIN_FOOD, self.Role.HR, self.Role.SYS_ADMIN]

    @property
    def is_hr(self):
        return self.role == self.Role.HR

    @property
    def is_sys_admin(self):
        return self.role == self.Role.SYS_ADMIN
