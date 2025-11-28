# Generated manually

from django.db import migrations, models


def rename_desserts_table_to_base_desserts(apps, schema_editor):
    """تغییر نام جدول ManyToMany از desserts به base_desserts"""
    db_alias = schema_editor.connection.alias
    
    with schema_editor.connection.cursor() as cursor:
        # بررسی وجود جدول
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'food_management_dailymenu_desserts'
            );
        """)
        table_exists = cursor.fetchone()[0]
        
        if table_exists:
            # تغییر نام ستون dessert_id به basedessert_id (اگر وجود داشته باشد)
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'food_management_dailymenu_desserts'
                AND column_name = 'dessert_id';
            """)
            column_exists = cursor.fetchone()
            if column_exists:
                cursor.execute("""
                    ALTER TABLE food_management_dailymenu_desserts
                    RENAME COLUMN dessert_id TO basedessert_id;
                """)
            
            # تغییر نام جدول
            cursor.execute("""
                ALTER TABLE food_management_dailymenu_desserts
                RENAME TO food_management_dailymenu_base_desserts;
            """)
            
            # تغییر نام Foreign Key constraint اگر وجود داشته باشد
            cursor.execute("""
                SELECT constraint_name 
                FROM information_schema.table_constraints 
                WHERE table_name = 'food_management_dailymenu_base_desserts'
                AND constraint_type = 'FOREIGN KEY'
                AND constraint_name LIKE '%dessert_id%';
            """)
            constraints = cursor.fetchall()
            for constraint in constraints:
                old_name = constraint[0]
                # تغییر نام constraint به base_dessert_id
                new_name = old_name.replace('dessert_id', 'basedessert_id')
                cursor.execute(f"""
                    ALTER TABLE food_management_dailymenu_base_desserts
                    RENAME CONSTRAINT {old_name} TO {new_name};
                """)


def reverse_rename_base_desserts_to_desserts(apps, schema_editor):
    """برگرداندن تغییرات"""
    db_alias = schema_editor.connection.alias
    
    with schema_editor.connection.cursor() as cursor:
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'food_management_dailymenu_base_desserts'
            );
        """)
        table_exists = cursor.fetchone()[0]
        
        if table_exists:
            cursor.execute("""
                ALTER TABLE food_management_dailymenu_base_desserts
                RENAME TO food_management_dailymenu_desserts;
            """)


class Migration(migrations.Migration):

    dependencies = [
        ('food_management', '0033_dessert_center'),
    ]

    operations = [
        # جدا کردن تغییرات در state از تغییرات در دیتابیس
        migrations.SeparateDatabaseAndState(
            database_operations=[
                # تغییر نام جدول در دیتابیس
                migrations.RunPython(
                    rename_desserts_table_to_base_desserts,
                    reverse_rename_base_desserts_to_desserts
                ),
            ],
            state_operations=[
                # تغییر نام فیلد در state (بدون تغییر در دیتابیس)
                migrations.RenameField(
                    model_name='dailymenu',
                    old_name='desserts',
                    new_name='base_desserts',
                ),
            ],
        ),
    ]

