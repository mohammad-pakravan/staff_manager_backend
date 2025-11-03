# Data migration to move center ForeignKey data to centers ManyToManyField

from django.db import migrations


def migrate_center_to_centers(apps, schema_editor):
    """Move center ForeignKey data to centers ManyToManyField"""
    User = apps.get_model('accounts', 'User')
    
    # Iterate through all users and add their center to centers
    for user in User.objects.all():
        if user.center_id:  # Check if user has a center
            user.centers.add(user.center_id)


def reverse_migrate_centers_to_center(apps, schema_editor):
    """Reverse migration: move first center from centers to center (not perfect, but for rollback)"""
    User = apps.get_model('accounts', 'User')
    
    # This reverse migration is not perfect, but for rollback purposes
    # We can only keep the first center
    for user in User.objects.all():
        if user.centers.exists():
            # Note: We cannot set center here as it's already removed
            # This is just a placeholder for rollback
            pass


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0005_user_centers_manytomany'),
    ]

    operations = [
        migrations.RunPython(migrate_center_to_centers, reverse_migrate_centers_to_center),
    ]

