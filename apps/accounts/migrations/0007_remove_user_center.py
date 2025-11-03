# Remove old ForeignKey center field

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0006_migrate_center_to_centers'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='user',
            name='center',
        ),
    ]

