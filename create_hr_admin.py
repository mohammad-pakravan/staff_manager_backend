#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.dev')
django.setup()

from apps.accounts.models import User
from apps.centers.models import Center

print("=== Creating HR Admin User ===")

# Get first center
center = Center.objects.first()
if not center:
    print("No center found!")
    sys.exit(1)

print(f"Using center: {center.name}")

# Create HR admin user
hr_admin, created = User.objects.get_or_create(
    username='hr_admin',
    defaults={
        'email': 'hr_admin@example.com',
        'first_name': 'HR',
        'last_name': 'Admin',
        'employee_number': 'HR001',
        'role': 'hr',
        'center': center,
        'phone_number': '09123456790',
        'max_reservations_per_day': 3,
        'max_guest_reservations_per_day': 2
    }
)

if created:
    hr_admin.set_password('hr123')
    hr_admin.save()
    print(f"Created HR admin: {hr_admin.username} (Center: {hr_admin.center.name})")
else:
    print(f"HR admin already exists: {hr_admin.username} (Center: {hr_admin.center.name})")

print("HR admin user ready!")
