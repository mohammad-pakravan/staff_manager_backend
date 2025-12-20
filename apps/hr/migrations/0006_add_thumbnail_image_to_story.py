# Generated manually - Add thumbnail_image column if it doesn't exist

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hr', '0005_story'),
    ]

    operations = [
        migrations.AddField(
            model_name='story',
            name='thumbnail_image',
            field=models.ImageField(blank=True, null=True, upload_to='stories/', verbose_name='تصویر شاخص'),
        ),
    ]

