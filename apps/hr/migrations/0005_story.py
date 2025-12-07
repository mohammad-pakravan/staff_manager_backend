# Generated manually

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('centers', '0005_remove_center_address_remove_center_city_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('hr', '0004_phonebook'),
    ]

    operations = [
        migrations.CreateModel(
            name='Story',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.TextField(blank=True, null=True, verbose_name='متن')),
                ('thumbnail_image', models.ImageField(blank=True, null=True, upload_to='stories/', verbose_name='تصویر شاخص')),
                ('content_file', models.FileField(blank=True, help_text='می\u200cتواند عکس یا ویدیو باشد', null=True, upload_to='stories/content/', verbose_name='محتوای قابل نمایش (عکس یا ویدیو)')),
                ('is_active', models.BooleanField(default=True, verbose_name='فعال')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='تاریخ بروزرسانی')),
                ('centers', models.ManyToManyField(related_name='stories', to='centers.center', verbose_name='مراکز')),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='created_stories', to=settings.AUTH_USER_MODEL, verbose_name='ایجاد شده توسط')),
            ],
            options={
                'verbose_name': 'استوری',
                'verbose_name_plural': 'استوری\u200cها',
                'ordering': ['-created_at'],
            },
        ),
    ]






