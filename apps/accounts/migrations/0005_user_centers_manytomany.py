# Generated manually for changing center ForeignKey to centers ManyToManyField

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0004_user_max_guest_reservations_per_day'),
        ('centers', '0002_alter_center_phone'),
    ]

    operations = [
        # Step 1: Add the new ManyToManyField (temporary, nullable)
        migrations.AddField(
            model_name='user',
            name='centers',
            field=models.ManyToManyField(
                blank=True,
                related_name='users',
                to='centers.center',
                verbose_name='مراکز'
            ),
        ),
        # Step 2: Data migration will run in next migration
        # Step 3: Remove old ForeignKey will be done after data migration
    ]

