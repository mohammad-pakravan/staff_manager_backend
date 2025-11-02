#!/usr/bin/env python
"""
اسکریپت پر کردن دیتابیس با داده‌های نمونه
برای تست سیستم مدیریت پرسنل
"""

import os
import django
from django.conf import settings
from decimal import Decimal

# تنظیم Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.dev')
django.setup()

from apps.accounts.models import User
from apps.centers.models import Center
from apps.food_management.models import (
    MealType, BaseMeal, MealOption, Restaurant,
    DailyMenu, FoodReservation, GuestReservation
)
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
        },
        {
            'username': 'test',
            'email': 'test@company.com',
            'first_name': 'محمد',
            'last_name': 'پاکروان',
            'employee_number': 'TEST001',
            'role': User.Role.EMPLOYEE,
            'center': centers[0]
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
    """ایجاد نوع وعده غذایی - فقط ناهار"""
    print("\n🍽️ ایجاد نوع وعده غذایی...")
    
    from datetime import time as dt_time
    
    # فقط ناهار
    meal_type_data = {
        'name': 'ناهار',
        'start_time': dt_time(12, 0, 0),
        'end_time': dt_time(14, 0, 0)
    }
    
        meal_type, created = MealType.objects.get_or_create(
            name=meal_type_data['name'],
            defaults=meal_type_data
        )
    
        if created:
            print(f"✅ نوع وعده '{meal_type.name}' ایجاد شد")
        else:
            print(f"ℹ️ نوع وعده '{meal_type.name}' قبلاً وجود دارد")
    
    # حذف سایر MealType ها
    other_meal_types = MealType.objects.exclude(name='ناهار')
    if other_meal_types.exists():
        count = other_meal_types.count()
        other_meal_types.delete()
        print(f"🗑️ {count} نوع وعده دیگر حذف شد")
    
    return [meal_type]


def create_restaurants(centers):
    """ایجاد رستوران‌های نمونه"""
    print("\n🍴 ایجاد رستوران‌های نمونه...")
    
    restaurants_data = [
        # اصفهان
        {
            'name': 'رستوران سنتی اصفهان',
            'center': centers[0],
            'address': 'خیابان چهارباغ، رستوران سنتی',
            'phone': '031-11111111',
            'email': 'restaurant1_isfahan@company.com',
            'description': 'رستوران سنتی اصفهان با غذاهای محلی'
        },
        {
            'name': 'رستوران مدرن اصفهان',
            'center': centers[0],
            'address': 'خیابان چهارباغ، رستوران مدرن',
            'phone': '031-22222222',
            'email': 'restaurant2_isfahan@company.com',
            'description': 'رستوران مدرن اصفهان'
        },
        # تهران
        {
            'name': 'رستوران تهران',
            'center': centers[1],
            'address': 'خیابان ولیعصر، رستوران تهران',
            'phone': '021-11111111',
            'email': 'restaurant1_tehran@company.com',
            'description': 'رستوران تهران'
        },
        # مشهد
        {
            'name': 'رستوران مشهد',
            'center': centers[2],
            'address': 'خیابان امام رضا، رستوران مشهد',
            'phone': '051-11111111',
            'email': 'restaurant1_mashhad@company.com',
            'description': 'رستوران مشهد'
        },
        # شیراز
        {
            'name': 'رستوران شیراز',
            'center': centers[3],
            'address': 'خیابان زند، رستوران شیراز',
            'phone': '071-11111111',
            'email': 'restaurant1_shiraz@company.com',
            'description': 'رستوران شیراز'
        },
        # تبریز
        {
            'name': 'رستوران تبریز',
            'center': centers[4],
            'address': 'خیابان آزادی، رستوران تبریز',
            'phone': '041-11111111',
            'email': 'restaurant1_tabriz@company.com',
            'description': 'رستوران تبریز'
        }
    ]
    
    restaurants = []
    for restaurant_data in restaurants_data:
        restaurant, created = Restaurant.objects.get_or_create(
            name=restaurant_data['name'],
            center=restaurant_data['center'],
            defaults=restaurant_data
        )
        restaurants.append(restaurant)
        if created:
            print(f"✅ رستوران '{restaurant.name}' برای مرکز '{restaurant.center.name}' ایجاد شد")
        else:
            print(f"ℹ️ رستوران '{restaurant.name}' برای مرکز '{restaurant.center.name}' قبلاً وجود دارد")
    
    return restaurants


def create_base_meals(centers, meal_types):
    """ایجاد غذاهای پایه نمونه"""
    print("\n🍲 ایجاد غذاهای پایه نمونه...")
    
    base_meals_data = [
        # اصفهان
        {
            'title': 'قورمه سبزی',
            'description': 'غذای سنتی ایرانی با گوشت و سبزیجات',
            'meal_type': meal_types[0],  # ناهار
            'center': centers[0],
            'is_active': True
        },
        {
            'title': 'کباب کوبیده',
            'description': 'کباب کوبیده با برنج و سبزی',
            'meal_type': meal_types[0],  # ناهار
            'center': centers[0],
            'is_active': True
        },
        # تهران
        {
            'title': 'قیمه نثار',
            'description': 'غذای سنتی ایرانی',
            'meal_type': meal_types[0],  # ناهار
            'center': centers[1],
            'is_active': True
        },
        {
            'title': 'جوجه کباب',
            'description': 'جوجه کباب با برنج',
            'meal_type': meal_types[0],  # ناهار
            'center': centers[1],
            'is_active': True
        },
        # مشهد
        {
            'title': 'زرشک پلو',
            'description': 'زرشک پلو با مرغ',
            'meal_type': meal_types[0],  # ناهار
            'center': centers[2],
            'is_active': True
        },
        # شیراز
        {
            'title': 'کوفته تبریزی',
            'description': 'کوفته تبریزی با برنج',
            'meal_type': meal_types[0],  # ناهار
            'center': centers[3],
            'is_active': True
        },
        # تبریز
        {
            'title': 'کباب بختیاری',
            'description': 'کباب بختیاری با برنج',
            'meal_type': meal_types[0],  # ناهار
            'center': centers[4],
            'is_active': True
        }
    ]
    
    base_meals = []
    for base_meal_data in base_meals_data:
        base_meal, created = BaseMeal.objects.get_or_create(
            title=base_meal_data['title'],
            center=base_meal_data['center'],
            defaults=base_meal_data
        )
        base_meals.append(base_meal)
        if created:
            print(f"✅ غذای پایه '{base_meal.title}' برای مرکز '{base_meal.center.name}' ایجاد شد")
        else:
            print(f"ℹ️ غذای پایه '{base_meal.title}' برای مرکز '{base_meal.center.name}' قبلاً وجود دارد")
    
    return base_meals


def create_meal_options(restaurants, base_meals):
    """ایجاد گزینه‌های غذا (MealOption) - این غذاهای اصلی هستند که رزرو می‌شوند"""
    print("\n🍽️ ایجاد گزینه‌های غذا...")
    
    # نگاشت مرکز به رستوران
    center_restaurants = {}
    for restaurant in restaurants:
        if restaurant.center not in center_restaurants:
            center_restaurants[restaurant.center] = []
        center_restaurants[restaurant.center].append(restaurant)
    
    meal_options_data = []
    
    for base_meal in base_meals:
        # پیدا کردن رستوران‌های مرکز این غذای پایه
        center_rests = center_restaurants.get(base_meal.center, [])
        if not center_rests:
            continue
        
        # برای هر غذای پایه، چند گزینه غذا ایجاد می‌کنیم
        restaurant = center_rests[0]  # رستوران اول مرکز
        
        if base_meal.title == 'قورمه سبزی':
            meal_options_data.extend([
                {
                    'base_meal': base_meal,
                    'restaurant': restaurant,
                    'title': 'قورمه سبزی - با برنج ایرانی',
                    'description': 'قورمه سبزی با برنج ایرانی مرغوب',
                    'price': Decimal('25000.00'),
                    'is_default': True,
                    'sort_order': 1
                },
                {
                    'base_meal': base_meal,
                    'restaurant': restaurant,
                    'title': 'قورمه سبزی - با برنج خارجی',
                    'description': 'قورمه سبزی با برنج خارجی',
                    'price': Decimal('28000.00'),
                    'is_default': False,
                    'sort_order': 2
                },
                {
                    'base_meal': base_meal,
                    'restaurant': restaurant,
                    'title': 'قورمه سبزی - با گوشت گوسفندی',
                    'description': 'قورمه سبزی با گوشت گوسفندی تازه',
                    'price': Decimal('35000.00'),
                    'is_default': False,
                    'sort_order': 3
                }
            ])
        elif base_meal.title == 'کباب کوبیده':
            meal_options_data.extend([
                {
                    'base_meal': base_meal,
                    'restaurant': restaurant,
                    'title': 'کباب کوبیده - با برنج',
                    'description': 'کباب کوبیده با برنج و سبزی',
                    'price': Decimal('30000.00'),
                    'is_default': True,
                    'sort_order': 1
                },
                {
                    'base_meal': base_meal,
                    'restaurant': restaurant,
                    'title': 'کباب کوبیده - با نان',
                    'description': 'کباب کوبیده با نان سنتی',
                    'price': Decimal('28000.00'),
                    'is_default': False,
                    'sort_order': 2
                }
            ])
        elif base_meal.title == 'آش رشته':
            meal_options_data.append({
                'base_meal': base_meal,
                'restaurant': restaurant,
                'title': 'آش رشته سنتی',
                'description': 'آش رشته سنتی با نعنا و پیازداغ',
                'price': Decimal('20000.00'),
                'is_default': True,
                'sort_order': 1
            })
        elif base_meal.title == 'قیمه نثار':
            meal_options_data.extend([
                {
                    'base_meal': base_meal,
                    'restaurant': restaurant,
                    'title': 'قیمه نثار - با برنج',
                    'description': 'قیمه نثار با برنج',
                    'price': Decimal('22000.00'),
                    'is_default': True,
                    'sort_order': 1
                }
            ])
        elif base_meal.title == 'جوجه کباب':
            meal_options_data.extend([
                {
                    'base_meal': base_meal,
                    'restaurant': restaurant,
                    'title': 'جوجه کباب - با برنج',
                    'description': 'جوجه کباب با برنج',
                    'price': Decimal('27000.00'),
                    'is_default': True,
                    'sort_order': 1
                }
            ])
        elif base_meal.title == 'زرشک پلو':
            meal_options_data.extend([
                {
                    'base_meal': base_meal,
                    'restaurant': restaurant,
                    'title': 'زرشک پلو - با مرغ',
                    'description': 'زرشک پلو با مرغ',
                    'price': Decimal('26000.00'),
                    'is_default': True,
                    'sort_order': 1
                }
            ])
        elif base_meal.title == 'کوفته تبریزی':
            meal_options_data.extend([
                {
                    'base_meal': base_meal,
                    'restaurant': restaurant,
                    'title': 'کوفته تبریزی - با برنج',
                    'description': 'کوفته تبریزی با برنج',
                    'price': Decimal('24000.00'),
                    'is_default': True,
                    'sort_order': 1
                }
            ])
        elif base_meal.title == 'کباب بختیاری':
            meal_options_data.extend([
                {
                    'base_meal': base_meal,
                    'restaurant': restaurant,
                    'title': 'کباب بختیاری - با برنج',
                    'description': 'کباب بختیاری با برنج',
                    'price': Decimal('32000.00'),
                    'is_default': True,
                    'sort_order': 1
                }
            ])
        else:
            # برای سایر غذاها یک گزینه پیش‌فرض ایجاد می‌کنیم
            meal_options_data.append({
                'base_meal': base_meal,
                'restaurant': restaurant,
                'title': f'{base_meal.title} - پیش‌فرض',
                'description': base_meal.description or '',
                'price': Decimal('25000.00'),
                'is_default': True,
                'sort_order': 1
            })
    
    meal_options = []
    for meal_option_data in meal_options_data:
        meal_option, created = MealOption.objects.get_or_create(
            title=meal_option_data['title'],
            restaurant=meal_option_data['restaurant'],
            base_meal=meal_option_data['base_meal'],
            defaults=meal_option_data
        )
        meal_options.append(meal_option)
        if created:
            print(f"✅ گزینه غذا '{meal_option.title}' برای رستوران '{meal_option.restaurant.name}' ایجاد شد")
        else:
            print(f"ℹ️ گزینه غذا '{meal_option.title}' برای رستوران '{meal_option.restaurant.name}' قبلاً وجود دارد")
    
    return meal_options


def create_daily_menus(centers, meal_types, meal_options):
    """ایجاد منوهای روزانه - فقط ناهار"""
    print("\n📋 ایجاد منوهای روزانه...")
    
    # نگاشت مرکز به meal_options
    center_meal_options = {}
    for meal_option in meal_options:
        center = meal_option.restaurant.center
        if center not in center_meal_options:
            center_meal_options[center] = []
        center_meal_options[center].append(meal_option)
    
    daily_menus = []
    meal_type = meal_types[0]  # فقط ناهار
    
    # ایجاد منو برای هر مرکز
    for center in centers:
        # ایجاد منو برای امروز و فردا
        today_date = date.today()
        for day_offset in range(2):  # فقط امروز و فردا
            menu_date = today_date + timedelta(days=day_offset)
            
            # پیدا کردن meal_options مربوط به این مرکز
            center_meal_opts = center_meal_options.get(center, [])
            
            # فیلتر کردن meal_options بر اساس meal_type
            filtered_meal_options = [
                opt for opt in center_meal_opts 
                if opt.base_meal.meal_type == meal_type
            ]
            
            if filtered_meal_options:
                daily_menu, created = DailyMenu.objects.get_or_create(
                    center=center,
                    date=menu_date,
                    meal_type=meal_type,
                    defaults={
                        'max_reservations_per_meal': 100,
                        'is_available': True
                    }
                )
                
                # اضافه کردن meal_options به daily_menu
                for meal_option in filtered_meal_options:
                    if meal_option not in daily_menu.meal_options.all():
                        daily_menu.meal_options.add(meal_option)
                
                daily_menus.append(daily_menu)
                
                if created:
                    print(f"✅ منوی روزانه برای مرکز '{center.name}' در تاریخ {menu_date} و وعده '{meal_type.name}' ایجاد شد")
                else:
                    print(f"ℹ️ منوی روزانه برای مرکز '{center.name}' در تاریخ {menu_date} و وعده '{meal_type.name}' به‌روزرسانی شد")
    
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


def create_food_reservations(users, daily_menus, meal_options):
    """ایجاد رزروهای نمونه"""
    print("\n🍽️ ایجاد رزروهای نمونه...")
    
    reservations = []
    
    # پیدا کردن daily_menu مربوط به امروز و ناهار
    today_date = date.today()
    today_daily_menus = [
        dm for dm in daily_menus 
        if dm.date == today_date and dm.meal_type.name == 'ناهار'
    ]
    
    if today_daily_menus and meal_options:
        # برای اولین daily_menu و اولین meal_option
        daily_menu = today_daily_menus[0]
        meal_option = meal_options[0]
        
        # بررسی اینکه این meal_option در daily_menu موجود است
        if meal_option in daily_menu.meal_options.all():
            # ایجاد رزرو برای کاربر test
            test_user = User.objects.filter(username='test').first()
            if test_user:
        reservation, created = FoodReservation.objects.get_or_create(
                    user=test_user,
                    daily_menu=daily_menu,
                    meal_option=meal_option,
                    defaults={
                        'quantity': 2,
                        'status': 'reserved'
                    }
        )
        reservations.append(reservation)
        if created:
            print(f"✅ رزرو برای '{reservation.user.username}' ایجاد شد")
        else:
            print(f"ℹ️ رزرو برای '{reservation.user.username}' قبلاً وجود دارد")
    
    return reservations


def create_guest_reservations(users, daily_menus, meal_options):
    """ایجاد رزروهای مهمان نمونه"""
    print("\n👥 ایجاد رزروهای مهمان نمونه...")
    
    guest_reservations = []
    
    # پیدا کردن daily_menu مربوط به امروز و ناهار
    today_date = date.today()
    today_daily_menus = [
        dm for dm in daily_menus 
        if dm.date == today_date and dm.meal_type.name == 'ناهار'
    ]
    
    if today_daily_menus and meal_options:
        daily_menu = today_daily_menus[0]
        meal_option = meal_options[0]
        
        if meal_option in daily_menu.meal_options.all():
            test_user = User.objects.filter(username='test').first()
            if test_user:
        guest_reservation, created = GuestReservation.objects.get_or_create(
                    host_user=test_user,
                    daily_menu=daily_menu,
                    meal_option=meal_option,
                    guest_first_name='علی',
                    guest_last_name='رضایی',
                    defaults={
                        'status': 'reserved'
                    }
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
        
        # 4. ایجاد رستوران‌ها
        restaurants = create_restaurants(centers)
        
        # 5. ایجاد غذاهای پایه
        base_meals = create_base_meals(centers, meal_types)
        
        # 6. ایجاد گزینه‌های غذا
        meal_options = create_meal_options(restaurants, base_meals)
        
        # 7. ایجاد منوهای روزانه
        daily_menus = create_daily_menus(centers, meal_types, meal_options)
        
        # 9. ایجاد اطلاعیه‌ها
        announcements = create_announcements(centers, users)
        
        # 10. ایجاد رزروهای غذا
        reservations = create_food_reservations(users, daily_menus, meal_options)
        
        # 11. ایجاد رزروهای مهمان
        guest_reservations = create_guest_reservations(users, daily_menus, meal_options)
        
        print("\n" + "=" * 50)
        print("✅ دیتابیس با موفقیت پر شد!")
        print(f"📊 آمار نهایی:")
        print(f"   - مراکز: {len(centers)}")
        print(f"   - کاربران: {len(users)}")
        print(f"   - انواع وعده: {len(meal_types)}")
        print(f"   - رستوران‌ها: {len(restaurants)}")
        print(f"   - غذاهای پایه: {len(base_meals)}")
        print(f"   - گزینه‌های غذا: {len(meal_options)}")
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
        print("   - Test User: test / password123")
        
    except Exception as e:
        print(f"❌ خطا در پر کردن دیتابیس: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()