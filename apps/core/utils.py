"""
Utility functions for the core app
"""
import jdatetime
from datetime import datetime, date
from django.utils import timezone


def to_jalali_date(gregorian_date):
    """Convert Gregorian date to Jalali date"""
    if isinstance(gregorian_date, datetime):
        return jdatetime.datetime.fromgregorian(datetime=gregorian_date)
    elif isinstance(gregorian_date, date):
        return jdatetime.date.fromgregorian(date=gregorian_date)
    return gregorian_date


def to_gregorian_date(jalali_date):
    """Convert Jalali date to Gregorian date"""
    if isinstance(jalali_date, jdatetime.datetime):
        return jalali_date.togregorian()
    elif isinstance(jalali_date, jdatetime.date):
        return jalali_date.togregorian()
    return jalali_date


def get_jalali_now():
    """Get current Jalali datetime"""
    return jdatetime.datetime.now()


def format_jalali_date(jalali_date, format_str='%Y/%m/%d'):
    """Format Jalali date to string"""
    if isinstance(jalali_date, jdatetime.datetime):
        return jalali_date.strftime(format_str)
    elif isinstance(jalali_date, jdatetime.date):
        return jalali_date.strftime(format_str)
    return str(jalali_date)


def get_jalali_week_start():
    """Get start of current Jalali week"""
    now = get_jalali_now()
    return now - jdatetime.timedelta(days=now.weekday())


def get_jalali_week_end():
    """Get end of current Jalali week"""
    week_start = get_jalali_week_start()
    return week_start + jdatetime.timedelta(days=6)


