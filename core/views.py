"""
Views برای endpoint های عمومی
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from drf_spectacular.types import OpenApiTypes
import jdatetime


@extend_schema(
    summary='Server Time and Date in Gregorian and Jalali',
    description='Display server time and date in Gregorian and Jalali',
    tags=['Server'],
    responses={
        200: {
            'description': 'زمان و تاریخ سرور',
            'content': {
                'application/json': {
                    'example': {
                        'gregorian': {
                            'date': '2025-11-01',
                            'datetime': '2025-11-01 14:30:45',
                            'timestamp': 1730478045,
                            'timezone': 'UTC'
                        },
                        'jalali': {
                            'date': '1404/08/10',
                            'datetime': '1404/08/10 14:30:45',
                            'date_persian': '۱۰ آبان ۱۴۰۴',
                            'datetime_persian': '۱۰ آبان ۱۴۰۴ - ۱۴:۳۰:۴۵'
                        },
                        'time': {
                            'hour': 14,
                            'minute': 30,
                            'second': 45
                        }
                    }
                }
            }
        }
    }
)
@api_view(['GET'])
@permission_classes([AllowAny])
def server_time(request):
    """
    نمایش زمان و تاریخ سرور (هم شمسی و هم میلادی)
    """
    # زمان فعلی سرور
    server_datetime = timezone.now()
    
    # تاریخ و زمان میلادی
    gregorian_date = server_datetime.date()
    gregorian_datetime = server_datetime
    
    # تبدیل به تاریخ شمسی
    jalali_date = jdatetime.date.fromgregorian(date=gregorian_date)
    jalali_datetime = jdatetime.datetime.fromgregorian(datetime=server_datetime)
    
    # نام ماه‌های فارسی
    persian_months = [
        'فروردین', 'اردیبهشت', 'خرداد', 'تیر', 'مرداد', 'شهریور',
        'مهر', 'آبان', 'آذر', 'دی', 'بهمن', 'اسفند'
    ]
    
    # تبدیل اعداد به فارسی
    def to_persian_digits(text):
        """تبدیل اعداد انگلیسی به فارسی"""
        persian_digits = '۰۱۲۳۴۵۶۷۸۹'
        english_digits = '0123456789'
        for en, fa in zip(english_digits, persian_digits):
            text = text.replace(en, fa)
        return text
    
    # ساخت تاریخ فارسی
    try:
        date_persian = f"{to_persian_digits(str(jalali_date.day))} {persian_months[jalali_date.month - 1]} {to_persian_digits(str(jalali_date.year))}"
        datetime_persian = f"{to_persian_digits(str(jalali_datetime.day))} {persian_months[jalali_datetime.month - 1]} {to_persian_digits(str(jalali_datetime.year))} - {to_persian_digits(jalali_datetime.strftime('%H:%M:%S'))}"
    except Exception:
        # اگر خطایی رخ داد، از فرمت ساده استفاده می‌کنیم
        date_persian = jalali_date.strftime('%d %B %Y')
        datetime_persian = jalali_datetime.strftime('%d %B %Y - %H:%M:%S')
    
    return Response({
        'gregorian': {
            'date': gregorian_date.strftime('%Y-%m-%d'),
            'datetime': gregorian_datetime.strftime('%Y-%m-%d %H:%M:%S'),
            'timestamp': int(server_datetime.timestamp()),
            'timezone': str(server_datetime.tzinfo) if server_datetime.tzinfo else None,
        },
        'jalali': {
            'date': jalali_date.strftime('%Y/%m/%d'),
            'datetime': jalali_datetime.strftime('%Y/%m/%d %H:%M:%S'),
            'date_persian': date_persian,
            'datetime_persian': datetime_persian,
        },
        'time': {
            'hour': server_datetime.hour,
            'minute': server_datetime.minute,
            'second': server_datetime.second,
        }
    })

