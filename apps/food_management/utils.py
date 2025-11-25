"""
توابع مشترک برای food_management و اپ‌های مرتبط
"""
from datetime import datetime
import jdatetime


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

