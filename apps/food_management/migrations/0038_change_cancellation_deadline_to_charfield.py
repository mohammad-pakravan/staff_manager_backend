# Generated manually

from django.db import migrations, models


def convert_datetime_to_string(apps, schema_editor):
    """تبدیل مقادیر datetime به string (شمسی)"""
    # این تابع می‌تواند داده‌های موجود را تبدیل کند
    # اما چون کاربر می‌خواهد string ذخیره شود، می‌توانیم این را خالی بگذاریم
    # یا داده‌های موجود را پاک کنیم
    pass


def reverse_convert_string_to_datetime(apps, schema_editor):
    """برگرداندن به datetime (اگر نیاز بود)"""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('food_management', '0037_change_dessert_to_dessert_option'),
    ]

    operations = [
        # تبدیل cancellation_deadline از DateTimeField به CharField در DailyMenuMealOption
        migrations.AlterField(
            model_name='dailymenumealoption',
            name='cancellation_deadline',
            field=models.CharField(blank=True, max_length=50, null=True, verbose_name='مهلت لغو'),
        ),
        # تبدیل cancellation_deadline از DateTimeField به CharField در DailyMenuDessertOption
        migrations.AlterField(
            model_name='dailymenudessertoption',
            name='cancellation_deadline',
            field=models.CharField(blank=True, max_length=50, null=True, verbose_name='مهلت لغو'),
        ),
        # تبدیل cancellation_deadline از DateTimeField به CharField در FoodReservation
        migrations.AlterField(
            model_name='foodreservation',
            name='cancellation_deadline',
            field=models.CharField(blank=True, max_length=50, null=True, verbose_name='مهلت لغو'),
        ),
        # تبدیل cancellation_deadline از DateTimeField به CharField در GuestReservation
        migrations.AlterField(
            model_name='guestreservation',
            name='cancellation_deadline',
            field=models.CharField(blank=True, max_length=50, null=True, verbose_name='مهلت لغو'),
        ),
        # تبدیل cancellation_deadline از DateTimeField به CharField در DessertReservation
        migrations.AlterField(
            model_name='dessertreservation',
            name='cancellation_deadline',
            field=models.CharField(blank=True, max_length=50, null=True, verbose_name='مهلت لغو'),
        ),
        # تبدیل cancellation_deadline از DateTimeField به CharField در GuestDessertReservation
        migrations.AlterField(
            model_name='guestdessertreservation',
            name='cancellation_deadline',
            field=models.CharField(blank=True, max_length=50, null=True, verbose_name='مهلت لغو'),
        ),
    ]


