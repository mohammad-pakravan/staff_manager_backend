# Generated manually

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('food_management', '0034_rename_desserts_to_base_desserts'),
    ]

    operations = [
        migrations.CreateModel(
            name='DailyMenuDessertOption',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200, verbose_name='عنوان دسر')),
                ('description', models.TextField(blank=True, null=True, verbose_name='توضیحات')),
                ('price', models.DecimalField(decimal_places=2, default=0, max_digits=10, verbose_name='قیمت')),
                ('quantity', models.PositiveIntegerField(default=0, verbose_name='تعداد')),
                ('reserved_quantity', models.PositiveIntegerField(default=0, verbose_name='تعداد رزرو شده')),
                ('is_default', models.BooleanField(default=False, verbose_name='گزینه پیش‌فرض')),
                ('cancellation_deadline', models.DateTimeField(blank=True, null=True, verbose_name='مهلت لغو')),
                ('sort_order', models.PositiveIntegerField(default=0, verbose_name='ترتیب نمایش')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='تاریخ بروزرسانی')),
                ('base_dessert', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='daily_menu_options', to='food_management.dessert', verbose_name='دسر پایه')),
                ('daily_menu', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='menu_dessert_options', to='food_management.dailymenu', verbose_name='منوی روزانه')),
            ],
            options={
                'verbose_name': 'اپشن دسر برای منو',
                'verbose_name_plural': 'اپشن‌های دسر برای منو',
                'ordering': ['sort_order', 'title'],
                'unique_together': {('daily_menu', 'base_dessert', 'title')},
            },
        ),
    ]

