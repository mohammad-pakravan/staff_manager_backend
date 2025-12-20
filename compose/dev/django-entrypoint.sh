#!/bin/sh

# Wait for database
echo "Waiting for database..."
while ! pg_isready -h db -p 5432; do
  sleep 1
done
echo "Database started"

# Run migrations
echo "Running migrations..."
python manage.py makemigrations
python manage.py migrate

# Create superuser if it doesn't exist
echo "Creating superuser..."
python manage.py shell -c "
from apps.accounts.models import User
import random
import string

# بررسی وجود کاربر admin
admin_user = User.objects.filter(username='admin').first()

if admin_user:
    # اگر کاربر وجود دارد، مطمئن شو که superuser است
    if not admin_user.is_superuser:
        admin_user.is_superuser = True
        admin_user.is_staff = True
        admin_user.save()
        print('Existing user promoted to superuser: admin')
    else:
        print('Superuser already exists: admin')
else:
    # اگر کاربر وجود ندارد، یک superuser جدید ایجاد کن
    # پیدا کردن employee_number منحصر به فرد
    employee_number = 'EMP001'
    counter = 1
    while User.objects.filter(employee_number=employee_number).exists():
        counter += 1
        employee_number = f'EMP{counter:03d}'
    
    try:
        User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='admin123',
            employee_number=employee_number,
            first_name='Admin',
            last_name='User',
            role='sys_admin',
            phone_number='1234567890'
        )
        print(f'Superuser created: admin/admin123 (employee_number: {employee_number})')
    except Exception as e:
        print(f'Error creating superuser: {e}')
        # اگر خطا داد، سعی کن با employee_number تصادفی
        random_suffix = ''.join(random.choices(string.digits, k=6))
        employee_number = f'ADM{random_suffix}'
        try:
            User.objects.create_superuser(
                username='admin',
                email='admin@example.com',
                password='admin123',
                employee_number=employee_number,
                first_name='Admin',
                last_name='User',
                role='sys_admin',
                phone_number='1234567890'
            )
            print(f'Superuser created with random employee_number: {employee_number}')
        except Exception as e2:
            print(f'Failed to create superuser: {e2}')
"

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Start server
echo "Starting development server..."
python manage.py runserver 0.0.0.0:8000
