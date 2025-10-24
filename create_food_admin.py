#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.dev')
django.setup()

from apps.accounts.models import User
from apps.centers.models import Center

print("=== Creating Food Admin User ===")

# Get first center
center = Center.objects.first()
if not center:
    print("No center found!")
    sys.exit(1)

print(f"Using center: {center.name}")

# Create food admin user
food_admin, created = User.objects.get_or_create(
    username='food_admin',
    defaults={
        'email': 'food_admin@example.com',
        'first_name': 'Food',
        'last_name': 'Admin',
        'employee_number': 'FA001',
        'role': 'admin_food',
        'center': center,
        'phone_number': '09123456789',
        'max_reservations_per_day': 5,
        'max_guest_reservations_per_day': 3
    }
)

if created:
    food_admin.set_password('food123')
    food_admin.save()
    print(f"Created food admin: {food_admin.username} (Center: {food_admin.center.name})")
else:
    print(f"Food admin already exists: {food_admin.username} (Center: {food_admin.center.name})")

print("Food admin user ready!")
