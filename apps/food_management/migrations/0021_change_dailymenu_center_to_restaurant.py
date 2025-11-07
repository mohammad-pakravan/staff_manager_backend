# Generated manually for changing DailyMenu center to restaurant

from django.db import migrations, models
import django.db.models.deletion


def migrate_center_to_restaurant(apps, schema_editor):
    """Migrate existing DailyMenu center to restaurant"""
    DailyMenu = apps.get_model('food_management', 'DailyMenu')
    Restaurant = apps.get_model('food_management', 'Restaurant')
    
    # برای هر DailyMenu با center مشخص، اولین رستوران فعال آن مرکز را پیدا کن
    for daily_menu in DailyMenu.objects.filter(restaurant__isnull=True):
        if daily_menu.center:
            # پیدا کردن اولین رستوران فعال آن مرکز
            restaurant = Restaurant.objects.filter(
                center=daily_menu.center,
                is_active=True
            ).first()
            
            if restaurant:
                daily_menu.restaurant = restaurant
                daily_menu.save()
            else:
                # اگر رستورانی پیدا نشد، اولین رستوران آن مرکز را انتخاب کن (حتی اگر غیرفعال باشد)
                restaurant = Restaurant.objects.filter(
                    center=daily_menu.center
                ).first()
                
                if restaurant:
                    daily_menu.restaurant = restaurant
                    daily_menu.save()
                else:
                    # اگر هیچ رستورانی پیدا نشد، خطا بده
                    raise ValueError(
                        f"برای DailyMenu با ID {daily_menu.id} و مرکز {daily_menu.center.name} "
                        f"هیچ رستورانی پیدا نشد. لطفاً ابتدا یک رستوران برای این مرکز ایجاد کنید."
                    )


def reverse_migrate_restaurant_to_center(apps, schema_editor):
    """Reverse migration: set center from restaurant"""
    DailyMenu = apps.get_model('food_management', 'DailyMenu')
    
    for daily_menu in DailyMenu.objects.filter(restaurant__isnull=False):
        if daily_menu.restaurant and daily_menu.restaurant.center:
            daily_menu.center = daily_menu.restaurant.center
            daily_menu.save()


class Migration(migrations.Migration):

    dependencies = [
        ('food_management', '0020_remove_dailymenu_meal_options_dailymenumealoption'),
    ]

    operations = [
        # Step 1: Add restaurant field as nullable
        migrations.AddField(
            model_name='dailymenu',
            name='restaurant',
            field=models.ForeignKey(
                null=True,
                blank=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='daily_menus',
                to='food_management.restaurant',
                verbose_name='رستوران'
            ),
        ),
        
        # Step 2: Migrate data from center to restaurant
        migrations.RunPython(migrate_center_to_restaurant, reverse_migrate_restaurant_to_center),
        
        # Step 3: Make restaurant non-nullable
        migrations.AlterField(
            model_name='dailymenu',
            name='restaurant',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='daily_menus',
                to='food_management.restaurant',
                verbose_name='رستوران'
            ),
        ),
        
        # Step 4: Remove unique_together constraint on center and date
        migrations.AlterUniqueTogether(
            name='dailymenu',
            unique_together=set(),
        ),
        
        # Step 5: Remove center field
        migrations.RemoveField(
            model_name='dailymenu',
            name='center',
        ),
        
        # Step 6: Add unique_together constraint on restaurant and date
        migrations.AlterUniqueTogether(
            name='dailymenu',
            unique_together={('restaurant', 'date')},
        ),
    ]

