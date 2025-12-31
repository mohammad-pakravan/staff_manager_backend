# Generated manually

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('food_management', '0033_dessert_center'),
    ]

    operations = [
        # فقط تغییر نام فیلد در state
        # تغییر نام جدول و ستون‌ها توسط migration 0039 (RenameModel) انجام می‌شود
        migrations.RenameField(
            model_name='dailymenu',
            old_name='desserts',
            new_name='base_desserts',
        ),
    ]

