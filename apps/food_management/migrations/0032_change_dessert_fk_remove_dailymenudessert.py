# Generated manually

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('food_management', '0031_alter_guestdessertreservation_dessert_and_more'),
    ]

    operations = [
        # Remove center field from Dessert
        migrations.RemoveField(
            model_name='dessert',
            name='center',
        ),
    ]

