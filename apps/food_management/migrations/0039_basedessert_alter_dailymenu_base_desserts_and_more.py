# Generated manually - Fix for duplicate table error
# این migration فقط state را تغییر می‌دهد، چون جدول food_management_dessert از قبل وجود دارد

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('food_management', '0038_change_cancellation_deadline_to_charfield'),
    ]

    operations = [
        # فقط تغییر state - جدول food_management_dessert از قبل وجود دارد
        migrations.SeparateDatabaseAndState(
            database_operations=[
                # هیچ تغییری در دیتابیس انجام نمی‌دهیم چون:
                # 1. جدول food_management_dessert از قبل وجود دارد
                # 2. BaseDessert از همان جدول استفاده می‌کند (db_table = 'food_management_dessert')
                # 3. فیلدهای base_desserts و base_dessert از قبل در migration های قبلی به‌روزرسانی شده‌اند
            ],
            state_operations=[
                # تغییر نام مدل از Dessert به BaseDessert در state
                migrations.RenameModel(
                    old_name='Dessert',
                    new_name='BaseDessert',
                ),
                # به‌روزرسانی فیلدهای مربوطه در state
                migrations.AlterField(
                    model_name='dailymenu',
                    name='base_desserts',
                    field=models.ManyToManyField(blank=True, related_name='daily_menus', to='food_management.basedessert', verbose_name='دسرهای پایه'),
                ),
                migrations.AlterField(
                    model_name='dailymenudessertoption',
                    name='base_dessert',
                    field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='daily_menu_options', to='food_management.basedessert', verbose_name='دسر پایه'),
                ),
            ],
        ),
    ]
