# Generated manually

from django.db import migrations, models


def set_default_phone_number(apps, schema_editor):
    """برای کاربران موجود که phone_number ندارند، یک مقدار پیش‌فرض می‌گذاریم"""
    User = apps.get_model('accounts', 'User')
    User.objects.filter(phone_number__isnull=True).update(phone_number='00000000000')
    User.objects.filter(phone_number='').update(phone_number='00000000000')


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0007_remove_user_center'),
    ]

    operations = [
        # ابتدا برای کاربران موجود که phone_number ندارند، مقدار پیش‌فرض می‌گذاریم
        migrations.RunPython(set_default_phone_number, reverse_code=migrations.RunPython.noop),
        # سپس فیلد را اجباری می‌کنیم
        migrations.AlterField(
            model_name='user',
            name='phone_number',
            field=models.CharField(max_length=15, verbose_name='شماره تلفن'),
        ),
    ]



