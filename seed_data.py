#!/usr/bin/env python
"""
اسکریپت پر کردن دیتابیس با داده‌های نمونه
برای تست سیستم مدیریت پرسنل
"""

import os
import django
from django.conf import settings

# تنظیم Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.dev')
django.setup()

from apps.accounts.models import User
from apps.centers.models import Center
from apps.food_management.models import MealType, Meal, WeeklyMenu, DailyMenu
from apps.hr.models import Announcement
from django.utils import timezone
from datetime import datetime, timedelta, date
import jdatetime


def create_centers():
    """ایجاد مراکز نمونه"""
    print("🏢 ایجاد مراکز...")
    
    centers_data = [
        {
            'name': 'مرکز اصفهان',
            'city': 'اصفهان',
            'address': 'خیابان چهارباغ، پلاک 123',
            'phone': '031-12345678',
            'email': 'isfahan@company.com'
        },
        {
            'name': 'مرکز تهران',
            'city': 'تهران',
            'address': 'خیابان ولیعصر، پلاک 456',
            'phone': '021-87654321',
            'email': 'tehran@company.com'
        },
        {
            'name': 'مرکز مشهد',
            'city': 'مشهد',
            'address': 'خیابان امام رضا، پلاک 789',
            'phone': '051-11223344',
            'email': 'mashhad@company.com'
        },
        {
            'name': 'مرکز شیراز',
            'city': 'شیراز',
            'address': 'خیابان زند، پلاک 321',
            'phone': '071-55667788',
            'email': 'shiraz@company.com'
        },
        {
            'name': 'مرکز تبریز',
            'city': 'تبریز',
            'address': 'خیابان آزادی، پلاک 654',
            'phone': '041-99887766',
            'email': 'tabriz@company.com'
        }
    ]
    
    centers = []
    for center_data in centers_data:
        center, created = Center.objects.get_or_create(
            name=center_data['name'],
            defaults=center_data
        )
        centers.append(center)
        if created:
            print(f"✅ مرکز '{center.name}' ایجاد شد")
        else:
            print(f"ℹ️ مرکز '{center.name}' قبلاً وجود دارد")
    
    return centers


def create_users(centers):
    """ایجاد کاربران نمونه"""
    print("\n👥 ایجاد کاربران...")
    
    users_data = [
        # System Admin
        {
            'username': 'admin',
            'email': 'admin@company.com',
            'first_name': 'مدیر',
            'last_name': 'سیستم',
            'employee_number': 'ADM001',
            'role': User.Role.SYS_ADMIN,
            'center': centers[0],
            'is_staff': True,
            'is_superuser': True
        },
        # Food Admins
        {
            'username': 'food_admin_isfahan',
            'email': 'food_admin_isfahan@company.com',
            'first_name': 'مدیر',
            'last_name': 'غذای اصفهان',
            'employee_number': 'FA001',
            'role': User.Role.ADMIN_FOOD,
            'center': centers[0],
            'is_staff': True
        },
        {
            'username': 'food_admin_tehran',
            'email': 'food_admin_tehran@company.com',
            'first_name': 'مدیر',
            'last_name': 'غذای تهران',
            'employee_number': 'FA002',
            'role': User.Role.ADMIN_FOOD,
            'center': centers[1],
            'is_staff': True
        },
        # HR Admins
        {
            'username': 'hr_admin_isfahan',
            'email': 'hr_admin_isfahan@company.com',
            'first_name': 'مدیر',
            'last_name': 'نیروی انسانی اصفهان',
            'employee_number': 'HR001',
            'role': User.Role.HR,
            'center': centers[0],
            'is_staff': True
        },
        {
            'username': 'hr_admin_tehran',
            'email': 'hr_admin_tehran@company.com',
            'first_name': 'مدیر',
            'last_name': 'نیروی انسانی تهران',
            'employee_number': 'HR002',
            'role': User.Role.HR,
            'center': centers[1],
            'is_staff': True
        },
        # Regular Employees
        {
            'username': 'employee_isfahan_1',
            'email': 'emp_isfahan_1@company.com',
            'first_name': 'احمد',
            'last_name': 'محمدی',
            'employee_number': 'EMP001',
            'role': User.Role.EMPLOYEE,
            'center': centers[0]
        },
        {
            'username': 'employee_isfahan_2',
            'email': 'emp_isfahan_2@company.com',
            'first_name': 'فاطمه',
            'last_name': 'احمدی',
            'employee_number': 'EMP002',
            'role': User.Role.EMPLOYEE,
            'center': centers[0]
        },
        {
            'username': 'employee_tehran_1',
            'email': 'emp_tehran_1@company.com',
            'first_name': 'علی',
            'last_name': 'رضایی',
            'employee_number': 'EMP003',
            'role': User.Role.EMPLOYEE,
            'center': centers[1]
        },
        {
            'username': 'employee_tehran_2',
            'email': 'emp_tehran_2@company.com',
            'first_name': 'زهرا',
            'last_name': 'حسینی',
            'employee_number': 'EMP004',
            'role': User.Role.EMPLOYEE,
            'center': centers[1]
        },
        {
            'username': 'employee_mashhad_1',
            'email': 'emp_mashhad_1@company.com',
            'first_name': 'حسن',
            'last_name': 'کریمی',
            'employee_number': 'EMP005',
            'role': User.Role.EMPLOYEE,
            'center': centers[2]
        }
    ]
    
    users = []
    for user_data in users_data:
        try:
            user, created = User.objects.get_or_create(
                username=user_data['username'],
                defaults=user_data
            )
            if created:
                user.set_password('password123')
                user.save()
                print(f"✅ کاربر '{user.username}' ایجاد شد")
            else:
                print(f"ℹ️ کاربر '{user.username}' قبلاً وجود دارد")
            users.append(user)
        except Exception as e:
            # اگر کاربر با شماره پرسنلی موجود وجود دارد، آن را پیدا کن
            try:
                user = User.objects.get(employee_number=user_data['employee_number'])
                print(f"ℹ️ کاربر با شماره پرسنلی '{user_data['employee_number']}' قبلاً وجود دارد: {user.username}")
                users.append(user)
            except User.DoesNotExist:
                print(f"❌ خطا در ایجاد کاربر '{user_data['username']}': {e}")
                # ایجاد کاربر با شماره پرسنلی جدید
                user_data['employee_number'] = f"{user_data['employee_number']}_{len(users)}"
                user = User.objects.create(**user_data)
                user.set_password('password123')
                user.save()
                print(f"✅ کاربر '{user.username}' با شماره پرسنلی جدید ایجاد شد")
                users.append(user)
    
    return users


def create_meal_types():
    """ایجاد انواع وعده‌های غذایی"""
    print("\n🍽️ ایجاد انواع وعده‌های غذایی...")
    
    meal_types_data = [
        {'name': 'صبحانه', 'start_time': '07:00', 'end_time': '09:00'},
        {'name': 'ناهار', 'start_time': '12:00', 'end_time': '14:00'},
        {'name': 'شام', 'start_time': '19:00', 'end_time': '21:00'},
        {'name': 'میان‌وعده', 'start_time': '15:00', 'end_time': '16:00'}
    ]
    
    meal_types = []
    for meal_type_data in meal_types_data:
        meal_type, created = MealType.objects.get_or_create(
            name=meal_type_data['name'],
            defaults=meal_type_data
        )
        meal_types.append(meal_type)
        if created:
            print(f"✅ نوع وعده '{meal_type.name}' ایجاد شد")
        else:
            print(f"ℹ️ نوع وعده '{meal_type.name}' قبلاً وجود دارد")
    
    return meal_types


def create_meals(centers, meal_types):
    """ایجاد غذاهای نمونه"""
    print("\n🍲 ایجاد غذاهای نمونه...")
    
    meals_data = [
        # اصفهان
        {
            'title': 'قورمه سبزی',
            'description': 'غذای سنتی ایرانی با گوشت و سبزیجات',
            'date': '2025-10-23',
            'meal_type': meal_types[1],  # ناهار
            'restaurant': 'رستوران سنتی اصفهان',
            'center': centers[0],
            'is_active': True
        },
        {
            'title': 'کباب کوبیده',
            'description': 'کباب کوبیده با برنج و سبزی',
            'date': '2025-10-23',
            'meal_type': meal_types[1],  # ناهار
            'restaurant': 'رستوران سنتی اصفهان',
            'center': centers[0],
            'is_active': True
        },
        {
            'title': 'آش رشته',
            'description': 'آش رشته سنتی',
            'date': '2025-10-23',
            'meal_type': meal_types[2],  # شام
            'restaurant': 'رستوران سنتی اصفهان',
            'center': centers[0],
            'is_active': True
        },
        # تهران
        {
            'title': 'قیمه نثار',
            'description': 'غذای سنتی ایرانی',
            'date': '2025-10-23',
            'meal_type': meal_types[1],  # ناهار
            'restaurant': 'رستوران تهران',
            'center': centers[1],
            'is_active': True
        },
        {
            'title': 'جوجه کباب',
            'description': 'جوجه کباب با برنج',
            'date': '2025-10-23',
            'meal_type': meal_types[1],  # ناهار
            'restaurant': 'رستوران تهران',
            'center': centers[1],
            'is_active': True
        },
        # مشهد
        {
            'title': 'زرشک پلو',
            'description': 'زرشک پلو با مرغ',
            'date': '2025-10-23',
            'meal_type': meal_types[1],  # ناهار
            'restaurant': 'رستوران مشهد',
            'center': centers[2],
            'is_active': True
        },
        # شیراز
        {
            'title': 'کوفته تبریزی',
            'description': 'کوفته تبریزی با برنج',
            'date': '2025-10-23',
            'meal_type': meal_types[1],  # ناهار
            'restaurant': 'رستوران شیراز',
            'center': centers[3],
            'is_active': True
        },
        # تبریز
        {
            'title': 'کباب بختیاری',
            'description': 'کباب بختیاری با برنج',
            'date': '2025-10-23',
            'meal_type': meal_types[1],  # ناهار
            'restaurant': 'رستوران تبریز',
            'center': centers[4],
            'is_active': True
        }
    ]
    
    meals = []
    for meal_data in meals_data:
        meal, created = Meal.objects.get_or_create(
            title=meal_data['title'],
            center=meal_data['center'],
            date=meal_data['date'],
            defaults=meal_data
        )
        meals.append(meal)
        if created:
            print(f"✅ غذا '{meal.title}' برای مرکز '{meal.center.name}' ایجاد شد")
        else:
            print(f"ℹ️ غذا '{meal.title}' برای مرکز '{meal.center.name}' قبلاً وجود دارد")
    
    return meals


def create_weekly_menus(centers, users):
    """ایجاد برنامه‌های هفتگی"""
    print("\n📅 ایجاد برنامه‌های هفتگی...")
    
    # تاریخ شروع هفته جاری
    today = jdatetime.date.today()
    week_start = today - jdatetime.timedelta(days=today.weekday())
    week_end = week_start + jdatetime.timedelta(days=6)
    
    # تبدیل به تاریخ میلادی
    week_start_gregorian = week_start.togregorian()
    week_end_gregorian = week_end.togregorian()
    
    weekly_menus = []
    for center in centers:
        weekly_menu, created = WeeklyMenu.objects.get_or_create(
            center=center,
            week_start_date=week_start_gregorian,
            defaults={
                'week_end_date': week_end_gregorian,
                'is_active': True,
                'created_by': users[0]  # System Admin
            }
        )
        weekly_menus.append(weekly_menu)
        if created:
            print(f"✅ برنامه هفتگی برای مرکز '{center.name}' ایجاد شد")
        else:
            print(f"ℹ️ برنامه هفتگی برای مرکز '{center.name}' قبلاً وجود دارد")
    
    return weekly_menus


def create_daily_menus(weekly_menus, meals):
    """ایجاد منوهای روزانه"""
    print("\n📋 ایجاد منوهای روزانه...")
    
    daily_menus = []
    for weekly_menu in weekly_menus:
        # ایجاد منو برای هر روز هفته
        for day_offset in range(7):
            menu_date = weekly_menu.week_start_date + timedelta(days=day_offset)
            
            # پیدا کردن غذاهای مربوط به این مرکز و تاریخ
            center_meals = [meal for meal in meals if meal.center == weekly_menu.center and meal.date == menu_date]
            
            # ایجاد منوی روزانه برای هر غذا
            for meal in center_meals:
                daily_menu, created = DailyMenu.objects.get_or_create(
                    weekly_menu=weekly_menu,
                    date=menu_date,
                    meal_type=meal.meal_type,
                    defaults={
                        'meal': meal,
                        'max_reservations': 100,
                        'current_reservations': 0,
                        'is_available': True
                    }
                )
                daily_menus.append(daily_menu)
                
                if created:
                    print(f"✅ منوی روزانه برای مرکز '{weekly_menu.center.name}' در تاریخ {menu_date} و وعده '{meal.meal_type.name}' ایجاد شد")
                else:
                    print(f"ℹ️ منوی روزانه برای مرکز '{weekly_menu.center.name}' در تاریخ {menu_date} و وعده '{meal.meal_type.name}' قبلاً وجود دارد")
    
    return daily_menus


def create_announcements(centers, users):
    """ایجاد اطلاعیه‌های نمونه"""
    print("\n📢 ایجاد اطلاعیه‌های نمونه...")
    
    announcements_data = [
        # اصفهان
        {
            'title': 'اطلاعیه مهم - مرکز اصفهان',
            'content': 'به اطلاع می‌رساند که جلسه عمومی پرسنل در روز پنج‌شنبه ساعت 10 صبح برگزار خواهد شد.',
            'publish_date': timezone.now(),
            'center': centers[0],
            'is_active': True,
            'created_by': users[3]  # HR Admin اصفهان
        },
        {
            'title': 'تغییر ساعت کاری',
            'content': 'ساعت کاری مرکز اصفهان از این هفته به 8 صبح تا 4 بعدازظهر تغییر یافت.',
            'publish_date': timezone.now() - timedelta(days=1),
            'center': centers[0],
            'is_active': True,
            'created_by': users[3]
        },
        # تهران
        {
            'title': 'اطلاعیه مهم - مرکز تهران',
            'content': 'کارگاه آموزشی مدیریت زمان در روز دوشنبه ساعت 2 بعدازظهر برگزار می‌شود.',
            'publish_date': timezone.now(),
            'center': centers[1],
            'is_active': True,
            'created_by': users[4]  # HR Admin تهران
        },
        {
            'title': 'برنامه تعطیلات',
            'content': 'مرکز تهران در روزهای 25 و 26 مهر تعطیل خواهد بود.',
            'publish_date': timezone.now() - timedelta(days=2),
            'center': centers[1],
            'is_active': True,
            'created_by': users[4]
        },
        # مشهد
        {
            'title': 'اطلاعیه مهم - مرکز مشهد',
            'content': 'جلسه بررسی عملکرد فصلی در روز چهارشنبه ساعت 9 صبح برگزار می‌شود.',
            'publish_date': timezone.now(),
            'center': centers[2],
            'is_active': True,
            'created_by': users[0]  # System Admin
        },
        # شیراز
        {
            'title': 'اطلاعیه مهم - مرکز شیراز',
            'content': 'برنامه بازدید از مرکز شیراز در روز شنبه ساعت 3 بعدازظهر.',
            'publish_date': timezone.now(),
            'center': centers[3],
            'is_active': True,
            'created_by': users[0]  # System Admin
        },
        # تبریز
        {
            'title': 'اطلاعیه مهم - مرکز تبریز',
            'content': 'کارگاه آموزشی امنیت اطلاعات در روز یکشنبه ساعت 10 صبح.',
            'publish_date': timezone.now(),
            'center': centers[4],
            'is_active': True,
            'created_by': users[0]  # System Admin
        }
    ]
    
    announcements = []
    for announcement_data in announcements_data:
        announcement, created = Announcement.objects.get_or_create(
            title=announcement_data['title'],
            center=announcement_data['center'],
            defaults=announcement_data
        )
        announcements.append(announcement)
        if created:
            print(f"✅ اطلاعیه '{announcement.title}' برای مرکز '{announcement.center.name}' ایجاد شد")
        else:
            print(f"ℹ️ اطلاعیه '{announcement.title}' برای مرکز '{announcement.center.name}' قبلاً وجود دارد")
    
    return announcements


def create_food_reservations(users, meals):
    """ایجاد رزروهای نمونه"""
    print("\n🍽️ ایجاد رزروهای نمونه...")
    
    from apps.food_management.models import FoodReservation
    
    reservations_data = [
        {
            'user': users[5],  # employee_isfahan_1
            'date': date(2025, 10, 23),
            'meal_type': meals[0].meal_type,
            'center': meals[0].center,
            'quantity': 1,
            'status': 'confirmed',
            'cancellation_deadline': timezone.now() + timedelta(hours=2)
        },
        {
            'user': users[6],  # employee_isfahan_2
            'date': date(2025, 10, 23),
            'meal_type': meals[0].meal_type,
            'center': meals[0].center,
            'quantity': 2,
            'status': 'confirmed',
            'cancellation_deadline': timezone.now() + timedelta(hours=2)
        },
        {
            'user': users[7],  # employee_tehran_1
            'date': date(2025, 10, 23),
            'meal_type': meals[3].meal_type,
            'center': meals[3].center,
            'quantity': 1,
            'status': 'confirmed',
            'cancellation_deadline': timezone.now() + timedelta(hours=2)
        },
        {
            'user': users[8],  # employee_tehran_2
            'date': date(2025, 10, 23),
            'meal_type': meals[3].meal_type,
            'center': meals[3].center,
            'quantity': 1,
            'status': 'pending',
            'cancellation_deadline': timezone.now() + timedelta(hours=2)
        }
    ]
    
    reservations = []
    for reservation_data in reservations_data:
        reservation, created = FoodReservation.objects.get_or_create(
            user=reservation_data['user'],
            date=reservation_data['date'],
            meal_type=reservation_data['meal_type'],
            center=reservation_data['center'],
            defaults=reservation_data
        )
        reservations.append(reservation)
        if created:
            print(f"✅ رزرو برای '{reservation.user.username}' ایجاد شد")
        else:
            print(f"ℹ️ رزرو برای '{reservation.user.username}' قبلاً وجود دارد")
    
    return reservations


def create_guest_reservations(users, meals):
    """ایجاد رزروهای مهمان نمونه"""
    print("\n👥 ایجاد رزروهای مهمان نمونه...")
    
    from apps.food_management.models import GuestReservation
    
    guest_reservations_data = [
        {
            'host_user': users[5],  # employee_isfahan_1
            'guest_first_name': 'محمد',
            'guest_last_name': 'احمدی',
            'date': date(2025, 10, 23),
            'meal_type': meals[0].meal_type,
            'center': meals[0].center,
            'status': 'confirmed',
            'cancellation_deadline': timezone.now() + timedelta(hours=2)
        },
        {
            'host_user': users[7],  # employee_tehran_1
            'guest_first_name': 'علی',
            'guest_last_name': 'رضایی',
            'date': date(2025, 10, 23),
            'meal_type': meals[3].meal_type,
            'center': meals[3].center,
            'status': 'confirmed',
            'cancellation_deadline': timezone.now() + timedelta(hours=2)
        }
    ]
    
    guest_reservations = []
    for guest_reservation_data in guest_reservations_data:
        guest_reservation, created = GuestReservation.objects.get_or_create(
            host_user=guest_reservation_data['host_user'],
            guest_first_name=guest_reservation_data['guest_first_name'],
            guest_last_name=guest_reservation_data['guest_last_name'],
            date=guest_reservation_data['date'],
            meal_type=guest_reservation_data['meal_type'],
            center=guest_reservation_data['center'],
            defaults=guest_reservation_data
        )
        guest_reservations.append(guest_reservation)
        if created:
            print(f"✅ رزرو مهمان برای '{guest_reservation.guest_first_name} {guest_reservation.guest_last_name}' ایجاد شد")
        else:
            print(f"ℹ️ رزرو مهمان برای '{guest_reservation.guest_first_name} {guest_reservation.guest_last_name}' قبلاً وجود دارد")
    
    return guest_reservations


def main():
    """تابع اصلی برای اجرای تمام مراحل"""
    print("🚀 شروع پر کردن دیتابیس با داده‌های نمونه...")
    print("=" * 50)
    
    try:
        # 1. ایجاد مراکز
        centers = create_centers()
        
        # 2. ایجاد کاربران
        users = create_users(centers)
        
        # 3. ایجاد انواع وعده‌های غذایی
        meal_types = create_meal_types()
        
        # 4. ایجاد غذاها
        meals = create_meals(centers, meal_types)
        
        # 5. ایجاد برنامه‌های هفتگی
        weekly_menus = create_weekly_menus(centers, users)
        
        # 6. ایجاد منوهای روزانه
        daily_menus = create_daily_menus(weekly_menus, meals)
        
        # 7. ایجاد اطلاعیه‌ها
        announcements = create_announcements(centers, users)
        
        # 8. ایجاد رزروهای غذا
        reservations = create_food_reservations(users, meals)
        
        # 9. ایجاد رزروهای مهمان
        guest_reservations = create_guest_reservations(users, meals)
        
        print("\n" + "=" * 50)
        print("✅ دیتابیس با موفقیت پر شد!")
        print(f"📊 آمار نهایی:")
        print(f"   - مراکز: {len(centers)}")
        print(f"   - کاربران: {len(users)}")
        print(f"   - انواع وعده: {len(meal_types)}")
        print(f"   - غذاها: {len(meals)}")
        print(f"   - برنامه‌های هفتگی: {len(weekly_menus)}")
        print(f"   - منوهای روزانه: {len(daily_menus)}")
        print(f"   - اطلاعیه‌ها: {len(announcements)}")
        print(f"   - رزروهای غذا: {len(reservations)}")
        print(f"   - رزروهای مهمان: {len(guest_reservations)}")
        print("\n🔑 اطلاعات ورود:")
        print("   - System Admin: admin / password123")
        print("   - Food Admin اصفهان: food_admin_isfahan / password123")
        print("   - Food Admin تهران: food_admin_tehran / password123")
        print("   - HR Admin اصفهان: hr_admin_isfahan / password123")
        print("   - HR Admin تهران: hr_admin_tehran / password123")
        print("   - Employee اصفهان 1: employee_isfahan_1 / password123")
        print("   - Employee اصفهان 2: employee_isfahan_2 / password123")
        print("   - Employee تهران 1: employee_tehran_1 / password123")
        print("   - Employee تهران 2: employee_tehran_2 / password123")
        print("   - Employee مشهد 1: employee_mashhad_1 / password123")
        
    except Exception as e:
        print(f"❌ خطا در پر کردن دیتابیس: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()