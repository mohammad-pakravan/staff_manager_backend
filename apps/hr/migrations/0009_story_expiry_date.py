# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hr', '0008_remove_story_centers'),
    ]

    operations = [
        migrations.AddField(
            model_name='story',
            name='expiry_date',
            field=models.DateTimeField(blank=True, help_text='بعد از این تاریخ فایل\u200cهای استوری به صورت خودکار پاک می\u200cشوند', null=True, verbose_name='تاریخ انقضا'),
        ),
    ]

