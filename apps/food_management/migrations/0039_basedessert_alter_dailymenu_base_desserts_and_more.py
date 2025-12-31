# Generated manually - Rename Dessert to BaseDessert

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('food_management', '0038_change_cancellation_deadline_to_charfield'),
    ]

    operations = [
        # تغییر نام مدل از Dessert به BaseDessert
        # این عملیات به طور خودکار همه foreign key ها و many-to-many ها را به‌روز می‌کند
        migrations.RenameModel(
            old_name='Dessert',
            new_name='BaseDessert',
        ),
    ]
