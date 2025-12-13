# Generated manually

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('food_management', '0036_remove_price_quantity_from_dessert'),
    ]

    operations = [
        # تغییر فیلد dessert به dessert_option در DessertReservation
        migrations.RemoveField(
            model_name='dessertreservation',
            name='dessert',
        ),
        migrations.AddField(
            model_name='dessertreservation',
            name='dessert_option',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='food_management.dailymenudessertoption', verbose_name='گزینه دسر'),
        ),
        # تغییر نام فیلد dessert_info به dessert_option_info
        migrations.RenameField(
            model_name='dessertreservation',
            old_name='dessert_info',
            new_name='dessert_option_info',
        ),
        # تغییر فیلد dessert به dessert_option در GuestDessertReservation
        migrations.RemoveField(
            model_name='guestdessertreservation',
            name='dessert',
        ),
        migrations.AddField(
            model_name='guestdessertreservation',
            name='dessert_option',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='food_management.dailymenudessertoption', verbose_name='گزینه دسر'),
        ),
        # تغییر نام فیلد dessert_info به dessert_option_info
        migrations.RenameField(
            model_name='guestdessertreservation',
            old_name='dessert_info',
            new_name='dessert_option_info',
        ),
    ]









