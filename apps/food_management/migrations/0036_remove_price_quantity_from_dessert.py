# Generated manually

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('food_management', '0035_create_dailymenudessertoption'),
    ]

    operations = [
        # حذف فیلدهای price, quantity, reserved_quantity از Dessert
        # این فیلدها دیگر در BaseDessert وجود ندارند و در DailyMenuDessertOption هستند
        migrations.RemoveField(
            model_name='dessert',
            name='price',
        ),
        migrations.RemoveField(
            model_name='dessert',
            name='quantity',
        ),
        migrations.RemoveField(
            model_name='dessert',
            name='reserved_quantity',
        ),
    ]






