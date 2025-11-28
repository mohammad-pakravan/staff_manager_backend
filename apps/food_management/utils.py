"""
توابع مشترک برای food_management و اپ‌های مرتبط
"""
from datetime import datetime
import jdatetime
from django.utils import timezone


def parse_date_filter(date_str):
    """تبدیل تاریخ شمسی یا میلادی به فرمت مناسب برای فیلتر"""
    if not date_str:
        return None
    
    # تبدیل به string برای اطمینان
    date_str = str(date_str).strip()
    
    try:
        # اگر تاریخ شمسی است (فرمت: 1404/08/02 یا 1403/10/25)
        if '/' in date_str:
            parts = date_str.split('/')
            if len(parts) == 3:
                year = int(parts[0].strip())
                month = int(parts[1].strip())
                day = int(parts[2].strip())
                # اگر سال 4 رقمی و بین 1300 تا 1500 باشد، احتمالاً شمسی است
                if 1300 <= year <= 1500:
                    jalali_date = jdatetime.date(year, month, day)
                    return jalali_date.togregorian()
        
        # اگر تاریخ میلادی است (فرمت: 2025-10-24)
        if '-' in date_str:
            return datetime.strptime(date_str, '%Y-%m-%d').date()
        
        # تلاش برای parse به عنوان میلادی
        return datetime.strptime(date_str, '%Y-%m-%d').date()
    except (ValueError, TypeError, AttributeError) as e:
        return None


def parse_datetime_filter(datetime_str):
    """تبدیل تاریخ و زمان شمسی یا میلادی به datetime میلادی"""
    if not datetime_str:
        return None
    
    # تبدیل به string برای اطمینان
    datetime_str = str(datetime_str).strip()
    
    # اگر خالی است، None برگردان
    if not datetime_str or datetime_str == '' or datetime_str.lower() == 'none':
        return None
    
    try:
        # اگر تاریخ شمسی است (فرمت: 1404/08/02 10:00 یا 1403/10/25 10:00:00)
        if '/' in datetime_str and not datetime_str.startswith('-'):
            # جدا کردن تاریخ و زمان
            parts = datetime_str.split(' ', 1)  # فقط یک بار split کن
            date_part = parts[0]
            time_part = parts[1] if len(parts) > 1 else '12:00'
            
            # parse کردن تاریخ شمسی
            date_parts = date_part.split('/')
            if len(date_parts) == 3:
                year_str = date_parts[0].strip()
                month_str = date_parts[1].strip()
                day_str = date_parts[2].strip()
                
                # چک کردن اینکه آیا سال منفی است یا نه
                if year_str.startswith('-'):
                    return None
                
                try:
                    year = int(year_str)
                    month = int(month_str)
                    day = int(day_str)
                except ValueError:
                    return None
                
                # اگر سال 4 رقمی و بین 1300 تا 1500 باشد، احتمالاً شمسی است
                if 1300 <= year <= 1500:
                    # parse کردن زمان
                    time_parts = time_part.split(':')
                    hour = int(time_parts[0].strip()) if len(time_parts) > 0 and time_parts[0].strip() else 12
                    minute = int(time_parts[1].strip()) if len(time_parts) > 1 and time_parts[1].strip() else 0
                    second = int(time_parts[2].strip()) if len(time_parts) > 2 and time_parts[2].strip() else 0
                    
                    # اعتبارسنجی مقادیر
                    if not (1 <= month <= 12) or not (1 <= day <= 31) or not (0 <= hour <= 23) or not (0 <= minute <= 59) or not (0 <= second <= 59):
                        return None
                    
                    # تبدیل به datetime شمسی و سپس میلادی
                    try:
                        jalali_datetime = jdatetime.datetime(year, month, day, hour, minute, second)
                        gregorian_datetime = jalali_datetime.togregorian()
                        
                        # تبدیل به timezone aware datetime
                        if timezone.is_naive(gregorian_datetime):
                            gregorian_datetime = timezone.make_aware(gregorian_datetime)
                        
                        return gregorian_datetime
                    except (ValueError, TypeError, AttributeError) as e:
                        return None
        
        # اگر تاریخ میلادی است (فرمت ISO: 2025-01-15T10:00:00Z یا 2025-01-15 10:00:00)
        # حذف Z از انتها اگر وجود دارد
        datetime_str_clean = datetime_str.rstrip('Zz')
        
        # تلاش برای parse به فرمت ISO
        try:
            # اگر Z وجود دارد، آن را به +00:00 تبدیل کن
            if datetime_str.endswith('Z') or datetime_str.endswith('z'):
                datetime_str_clean = datetime_str_clean.replace('Z', '+00:00').replace('z', '+00:00')
                if '+' not in datetime_str_clean and '-' not in datetime_str_clean[-6:]:
                    datetime_str_clean = datetime_str_clean + '+00:00'
            dt = datetime.fromisoformat(datetime_str_clean)
            if timezone.is_naive(dt):
                dt = timezone.make_aware(dt)
            return dt
        except ValueError:
            pass
        
        # تلاش برای parse به فرمت‌های دیگر
        formats = [
            '%Y-%m-%dT%H:%M:%S%z',
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%dT%H:%M',
            '%Y-%m-%d %H:%M',
        ]
        
        for fmt in formats:
            try:
                dt = datetime.strptime(datetime_str_clean, fmt)
                if timezone.is_naive(dt):
                    dt = timezone.make_aware(dt)
                return dt
            except ValueError:
                continue
        
        return None
    except (ValueError, TypeError, AttributeError) as e:
        return None

