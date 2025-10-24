from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, extend_schema_view
from drf_spectacular.types import OpenApiTypes
from django.db.models import Q, Count, Sum
from django.utils import timezone
from django.shortcuts import get_object_or_404
from datetime import datetime, timedelta
import jdatetime
from django.http import HttpResponse
from io import BytesIO
from apps.core.pagination import CustomPageNumberPagination


def parse_date_filter(date_str):
    """تبدیل تاریخ شمسی یا میلادی به فرمت مناسب برای فیلتر"""
    if not date_str:
        return None
    
    try:
        # اگر تاریخ شمسی است (فرمت: 1404/08/02)
        if '/' in date_str and len(date_str.split('/')) == 3:
            parts = date_str.split('/')
            if len(parts[0]) == 4:  # سال 4 رقمی (شمسی)
                jalali_date = jdatetime.date(int(parts[0]), int(parts[1]), int(parts[2]))
                return jalali_date.togregorian()
        
        # اگر تاریخ میلادی است (فرمت: 2025-10-24)
        return datetime.strptime(date_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return None


# Optional imports for export functionality
try:
    import openpyxl
    HAS_OPENPYXL = True
except ImportError:
    HAS_OPENPYXL = False

try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.utils import ImageReader
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False

from .models import (
    Meal, MealType, WeeklyMenu, DailyMenu, 
    FoodReservation, FoodReport, GuestReservation
)
from apps.centers.models import Center
from .serializers import (
    MealSerializer, MealTypeSerializer, WeeklyMenuSerializer,
    DailyMenuSerializer, FoodReservationSerializer,
    FoodReservationCreateSerializer, FoodReportSerializer,
    WeeklyMenuCreateSerializer, MealStatisticsSerializer,
    GuestReservationSerializer, GuestReservationCreateSerializer,
    SimpleFoodReservationSerializer, SimpleGuestReservationSerializer
)


# ========== Meal Management ==========

@extend_schema_view(
    get=extend_schema(
        operation_id='meal_list',
        summary='List Meals',
        description='Get list of all meals (only active meals for regular users)',
        tags=['Meals']
    ),
    post=extend_schema(
        operation_id='meal_create',
        summary='Create Meal',
        description='Create new meal (only for food admins and system admins)',
        tags=['Meals']
    )
)
class MealListCreateView(generics.ListCreateAPIView):
    """لیست و ایجاد غذاها"""
    queryset = Meal.objects.all()
    serializer_class = MealSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = CustomPageNumberPagination

    def get_queryset(self):
        # ادمین سیستم و ادمین غذا می‌توانند همه غذاها را ببینند
        # کاربران عادی فقط غذاهای مرکز خود را می‌بینند
        user = self.request.user
        if user.role in ['sys_admin', 'admin_food']:
            return Meal.objects.all()
        elif user.center:
            return Meal.objects.filter(is_active=True, center=user.center)
        return Meal.objects.none()
    
    def perform_create(self, serializer):
        # فقط ادمین‌های غذا و سیستم می‌توانند غذا ایجاد کنند
        user = self.request.user
        if user.role not in ['admin_food', 'sys_admin']:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("فقط ادمین‌های غذا می‌توانند غذا ایجاد کنند")
        
        # ادمین غذا و System Admin می‌توانند برای هر مرکزی غذا ایجاد کنند
        serializer.save()


@extend_schema_view(
    get=extend_schema(
        operation_id='meal_detail',
        summary='Get Meal Details',
        description='Get details of a specific meal',
        tags=['Meals']
    ),
    put=extend_schema(
        operation_id='meal_update',
        summary='Update Meal',
        description='Update meal completely (only for admins)',
        tags=['Meals']
    ),
    patch=extend_schema(
        operation_id='meal_partial_update',
        summary='Partial Update Meal',
        description='Partially update meal (only for admins)',
        tags=['Meals']
    ),
    delete=extend_schema(
        operation_id='meal_delete',
        summary='Delete Meal',
        description='Delete meal (only for admins)',
        tags=['Meals']
    )
)
class MealDetailView(generics.RetrieveUpdateDestroyAPIView):
    """جزئیات، ویرایش و حذف غذا"""
    queryset = Meal.objects.all()
    serializer_class = MealSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role in ['admin_food', 'sys_admin']:
            return Meal.objects.all()
        # کاربران عادی فقط غذاهای مرکز خود را می‌بینند
        elif user.center:
            return Meal.objects.filter(center=user.center)
        else:
            return Meal.objects.none()


# ========== Meal Type Management ==========

class MealTypeListView(generics.ListAPIView):
    """لیست انواع وعده غذایی"""
    queryset = MealType.objects.all()
    serializer_class = MealTypeSerializer
    permission_classes = [permissions.IsAuthenticated]


# ========== Weekly Menu Management ==========

class WeeklyMenuListCreateView(generics.ListCreateAPIView):
    """لیست و ایجاد برنامه‌های هفتگی"""
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return WeeklyMenuCreateSerializer
        return WeeklyMenuSerializer

    def get_queryset(self):
        user = self.request.user
        if user.role in ['sys_admin', 'admin_food']:
            return WeeklyMenu.objects.all()
        elif user.center:
            return WeeklyMenu.objects.filter(center=user.center)
        return WeeklyMenu.objects.none()

    def perform_create(self, serializer):
        user = self.request.user
        # ادمین غذا و System Admin می‌توانند برای هر مرکزی برنامه هفتگی ایجاد کنند
        serializer.save(created_by=user)


class WeeklyMenuDetailView(generics.RetrieveUpdateDestroyAPIView):
    """جزئیات برنامه هفتگی"""
    serializer_class = WeeklyMenuSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role in ['sys_admin', 'admin_food']:
            return WeeklyMenu.objects.all()
        elif user.center:
            return WeeklyMenu.objects.filter(center=user.center)
        return WeeklyMenu.objects.none()


# ========== Daily Menu Views ==========

class DailyMenuListView(generics.ListAPIView):
    """لیست منوهای روزانه"""
    serializer_class = DailyMenuSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        center_id = self.request.query_params.get('center')
        date = self.request.query_params.get('date')
        
        queryset = DailyMenu.objects.filter(is_available=True)
        
        # فیلتر بر اساس مرکز
        if center_id:
            try:
                center_id = int(center_id)
                queryset = queryset.filter(weekly_menu__center_id=center_id)
            except (ValueError, TypeError):
                # Invalid center_id, return empty queryset
                queryset = queryset.none()
        elif user.center and not user.is_admin:
            queryset = queryset.filter(weekly_menu__center=user.center)
        
        # فیلتر بر اساس تاریخ
        if date:
            try:
                from datetime import datetime
                # Validate date format
                datetime.strptime(date, '%Y-%m-%d')
                queryset = queryset.filter(date=date)
            except (ValueError, TypeError):
                # Invalid date format, return empty queryset
                queryset = queryset.none()
        else:
            # اگر تاریخ مشخص نشده، منوهای هفته جاری را نشان بده
            today = timezone.now().date()
            week_start = today - timedelta(days=today.weekday())
            week_end = week_start + timedelta(days=6)
            queryset = queryset.filter(date__range=[week_start, week_end])
        
        return queryset.order_by('date', 'meal_type__start_time')


# ========== Food Reservation Views ==========

@extend_schema_view(
    get=extend_schema(
        operation_id='food_reservation_list',
        summary='List Food Reservations',
        description='Get list of food reservations (admins: all, users: own reservations)',
        tags=['Reservations']
    ),
    post=extend_schema(
        operation_id='food_reservation_create',
        summary='Create Food Reservation',
        description='Create new food reservation for user',
        tags=['Reservations']
    )
)
class FoodReservationListCreateView(generics.ListCreateAPIView):
    """لیست و ایجاد رزروهای غذا"""
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = CustomPageNumberPagination

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return FoodReservationCreateSerializer
        return FoodReservationSerializer

    def get_queryset(self):
        user = self.request.user
        if user.role in ['admin_food', 'sys_admin']:
            return FoodReservation.objects.all()
        return FoodReservation.objects.filter(user=user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class FoodReservationDetailView(generics.RetrieveUpdateDestroyAPIView):
    """جزئیات رزرو غذا"""
    serializer_class = SimpleFoodReservationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role in ['admin_food', 'sys_admin']:
            return FoodReservation.objects.all()
        return FoodReservation.objects.filter(user=user)


@extend_schema(
    operation_id='user_reservation_limits',
    summary='Check User Reservation Limits',
    description='Check available and remaining reservations for user on specific date',
    responses={
        200: OpenApiTypes.OBJECT,
        400: OpenApiTypes.OBJECT
    }
)
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def user_reservation_limits(request):
    """بررسی محدودیت‌های رزرو کاربر"""
    user = request.user
    date = request.query_params.get('date')
    
    if not date:
        return Response({
            'error': 'تاریخ الزامی است'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # تبدیل تاریخ شمسی یا میلادی به فرمت مناسب
    parsed_date = parse_date_filter(date)
    if not parsed_date:
        return Response({
            'error': 'فرمت تاریخ نامعتبر است. از فرمت میلادی (2025-10-24) یا شمسی (1404/08/02) استفاده کنید'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    current_reservations = FoodReservation.get_user_date_reservations_count(user, parsed_date)
    available_slots = user.max_reservations_per_day - current_reservations
    
    return Response({
        'user': {
            'id': user.id,
            'username': user.username,
            'full_name': f"{user.first_name} {user.last_name}".strip(),
            'max_reservations_per_day': user.max_reservations_per_day
        },
        'date': date,
        'current_reservations': current_reservations,
        'available_slots': max(0, available_slots),
        'can_reserve': available_slots > 0
    })


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def cancel_reservation(request, reservation_id):
    """لغو رزرو غذا"""
    try:
        reservation = FoodReservation.objects.get(
            id=reservation_id,
            user=request.user
        )
        
        if reservation.cancel():
            return Response({
                'message': 'رزرو با موفقیت لغو شد.'
            })
        else:
            return Response({
                'error': 'امکان لغو این رزرو وجود ندارد.'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    except FoodReservation.DoesNotExist:
        return Response({
            'error': 'رزرو مورد نظر یافت نشد.'
        }, status=status.HTTP_404_NOT_FOUND)


# ========== Guest Reservation Views ==========

@extend_schema_view(
    get=extend_schema(
        operation_id='guest_reservation_list',
        summary='List Guest Reservations',
        description='Get list of guest reservations (admins: all, users: own guest reservations)',
        tags=['Guest Reservations']
    ),
    post=extend_schema(
        operation_id='guest_reservation_create',
        summary='Create Guest Reservation',
        description='Create food reservation for guest',
        tags=['Guest Reservations']
    )
)
class GuestReservationListCreateView(generics.ListCreateAPIView):
    """لیست و ایجاد رزروهای مهمان"""
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = CustomPageNumberPagination

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return GuestReservationCreateSerializer
        return GuestReservationSerializer

    def get_queryset(self):
        user = self.request.user
        if user.role in ['admin_food', 'sys_admin']:
            return GuestReservation.objects.all()
        return GuestReservation.objects.filter(host_user=user)

    def perform_create(self, serializer):
        serializer.save(host_user=self.request.user)


class GuestReservationDetailView(generics.RetrieveUpdateDestroyAPIView):
    """جزئیات رزرو مهمان"""
    serializer_class = SimpleGuestReservationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role in ['admin_food', 'sys_admin']:
            return GuestReservation.objects.all()
        return GuestReservation.objects.filter(host_user=user)


@extend_schema(
    operation_id='user_guest_reservation_limits',
    summary='Check User Guest Reservation Limits',
    description='Check available and remaining guest reservations for user on specific date',
    responses={
        200: OpenApiTypes.OBJECT,
        400: OpenApiTypes.OBJECT
    }
)
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def user_guest_reservation_limits(request):
    """بررسی محدودیت‌های رزرو مهمان کاربر"""
    user = request.user
    date = request.query_params.get('date')
    
    if not date:
        return Response({
            'error': 'تاریخ الزامی است'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # تبدیل تاریخ شمسی یا میلادی به فرمت مناسب
    parsed_date = parse_date_filter(date)
    if not parsed_date:
        return Response({
            'error': 'فرمت تاریخ نامعتبر است. از فرمت میلادی (2025-10-24) یا شمسی (1404/08/02) استفاده کنید'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    current_guest_reservations = GuestReservation.get_user_date_guest_reservations_count(user, parsed_date)
    available_slots = user.max_guest_reservations_per_day - current_guest_reservations
    
    return Response({
        'user': {
            'id': user.id,
            'username': user.username,
            'full_name': f"{user.first_name} {user.last_name}".strip(),
            'max_guest_reservations_per_day': user.max_guest_reservations_per_day
        },
        'date': date,
        'current_guest_reservations': current_guest_reservations,
        'available_slots': max(0, available_slots),
        'can_reserve_guest': available_slots > 0
    })


@extend_schema(
    operation_id='cancel_guest_reservation',
    summary='Cancel Guest Reservation',
    description='Cancel guest reservation by host user',
    responses={
        200: OpenApiTypes.OBJECT,
        400: OpenApiTypes.OBJECT,
        404: OpenApiTypes.OBJECT
    }
)
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def cancel_guest_reservation(request, reservation_id):
    """لغو رزرو مهمان"""
    try:
        reservation = GuestReservation.objects.get(
            id=reservation_id,
            host_user=request.user
        )
        
        if reservation.cancel():
            return Response({
                'message': 'رزرو مهمان با موفقیت لغو شد.'
            })
        else:
            return Response({
                'error': 'امکان لغو این رزرو مهمان وجود ندارد.'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    except GuestReservation.DoesNotExist:
        return Response({
            'error': 'رزرو مهمان مورد نظر یافت نشد.'
        }, status=status.HTTP_404_NOT_FOUND)


# ========== Statistics and Reports ==========

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def meal_statistics(request):
    """آمار کلی غذاها"""
    if not request.user.is_admin:
        return Response({
            'error': 'دسترسی غیرمجاز'
        }, status=status.HTTP_403_FORBIDDEN)
    
    today = timezone.now().date()
    
    stats = {
        'total_meals': Meal.objects.count(),
        'active_meals': Meal.objects.all().count(),
        'total_reservations': FoodReservation.objects.count(),
        'today_reservations': FoodReservation.objects.filter(
            daily_menu__date=today
        ).count(),
        'cancelled_reservations': FoodReservation.objects.filter(
            status='cancelled'
        ).count(),
        'served_reservations': FoodReservation.objects.filter(
            status='served'
        ).count(),
    }
    
    serializer = MealStatisticsSerializer(stats)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def center_reservations(request, center_id):
    """رزروهای یک مرکز خاص"""
    if not request.user.is_admin:
        return Response({
            'error': 'دسترسی غیرمجاز'
        }, status=status.HTTP_403_FORBIDDEN)
    
    center = get_object_or_404(Center, id=center_id)
    date = request.query_params.get('date')
    
    queryset = FoodReservation.objects.filter(
        daily_menu__weekly_menu__center=center
    )
    
    if date:
        parsed_date = parse_date_filter(date)
        if parsed_date:
            queryset = queryset.filter(daily_menu__date=parsed_date)
    
    serializer = SimpleFoodReservationSerializer(queryset, many=True)
    return Response(serializer.data)


# ========== Export Functions ==========

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def export_reservations_excel(request, center_id):
    """خروجی اکسل رزروها"""
    if not request.user.is_admin:
        return Response({
            'error': 'دسترسی غیرمجاز'
        }, status=status.HTTP_403_FORBIDDEN)
    
    if not HAS_OPENPYXL:
        return Response({
            'error': 'کتابخانه openpyxl نصب نشده است'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    center = get_object_or_404(Center, id=center_id)
    date = request.query_params.get('date')
    
    reservations = FoodReservation.objects.filter(
        daily_menu__weekly_menu__center=center
    )
    
    if date:
        parsed_date = parse_date_filter(date)
        if parsed_date:
            reservations = reservations.filter(daily_menu__date=parsed_date)
    
    # ایجاد فایل اکسل
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = f"رزروهای {center.name}"
    
    # هدرها
    headers = [
        'نام کاربر', 'تاریخ', 'وعده غذایی', 'نام غذا',
        'وضعیت', 'تاریخ رزرو', 'مهلت لغو'
    ]
    
    for col, header in enumerate(headers, 1):
        ws.cell(row=1, column=col, value=header)
    
    # داده‌ها
    for row, reservation in enumerate(reservations, 2):
        ws.cell(row=row, column=1, value=reservation.user.username)
        ws.cell(row=row, column=2, value=str(reservation.daily_menu.date))
        ws.cell(row=row, column=3, value=reservation.daily_menu.meal_type.name)
        ws.cell(row=row, column=4, value=reservation.meal.title if reservation.meal else 'نامشخص')
        ws.cell(row=row, column=5, value=reservation.get_status_display())
        ws.cell(row=row, column=6, value=str(reservation.reservation_date))
        ws.cell(row=row, column=7, value=str(reservation.cancellation_deadline))
    
    # ذخیره فایل
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="reservations_{center.name}_{date or "all"}.xlsx"'
    
    wb.save(response)
    return response


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def export_reservations_pdf(request, center_id):
    """خروجی PDF رزروها"""
    if not request.user.is_admin:
        return Response({
            'error': 'دسترسی غیرمجاز'
        }, status=status.HTTP_403_FORBIDDEN)
    
    if not HAS_REPORTLAB:
        return Response({
            'error': 'کتابخانه reportlab نصب نشده است'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    center = get_object_or_404(Center, id=center_id)
    date = request.query_params.get('date')
    
    reservations = FoodReservation.objects.filter(
        daily_menu__weekly_menu__center=center
    )
    
    if date:
        parsed_date = parse_date_filter(date)
        if parsed_date:
            reservations = reservations.filter(daily_menu__date=parsed_date)
    
    # ایجاد PDF
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    
    # عنوان
    p.setFont("Helvetica-Bold", 16)
    p.drawString(100, height - 50, f"گزارش رزروهای {center.name}")
    
    if date:
        p.setFont("Helvetica", 12)
        p.drawString(100, height - 80, f"تاریخ: {date}")
    
    # هدر جدول
    y_position = height - 120
    p.setFont("Helvetica-Bold", 10)
    headers = ['نام کاربر', 'تاریخ', 'وعده', 'غذا', 'وضعیت']
    x_positions = [100, 200, 300, 400, 500]
    
    for i, header in enumerate(headers):
        p.drawString(x_positions[i], y_position, header)
    
    # داده‌ها
    y_position -= 20
    p.setFont("Helvetica", 8)
    
    for reservation in reservations:
        if y_position < 100:  # صفحه جدید
            p.showPage()
            y_position = height - 50
        
        data = [
            reservation.user.username,
            str(reservation.daily_menu.date),
            reservation.daily_menu.meal_type.name,
            reservation.meal.title if reservation.meal else 'نامشخص',
            reservation.get_status_display()
        ]
        
        for i, item in enumerate(data):
            p.drawString(x_positions[i], y_position, str(item))
        
        y_position -= 15
    
    p.showPage()
    p.save()
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="reservations_{center.name}_{date or "all"}.pdf"'
    response.write(buffer.getvalue())
    buffer.close()
    
    return response


# ========== User Reservations ==========

@extend_schema(
    operation_id='user_reservations',
    summary='Get User Reservations',
    description='Get all reservations for the authenticated user',
    tags=['User Reservations']
)
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def user_reservations(request):
    """رزروهای کاربر"""
    user = request.user
    reservations = FoodReservation.objects.filter(user=user).order_by('-reservation_date')
    
    # فیلتر بر اساس تاریخ
    date = request.query_params.get('date')
    if date:
        parsed_date = parse_date_filter(date)
        if parsed_date:
            reservations = reservations.filter(daily_menu__date=parsed_date)
    
    # فیلتر بر اساس وضعیت
    status_filter = request.query_params.get('status')
    if status_filter:
        reservations = reservations.filter(status=status_filter)
    
    serializer = SimpleFoodReservationSerializer(reservations, many=True)
    return Response(serializer.data)


@extend_schema(
    operation_id='user_guest_reservations',
    summary='Get User Guest Reservations',
    description='Get all guest reservations made by the authenticated user',
    tags=['User Reservations']
)
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def user_guest_reservations(request):
    """رزروهای مهمان کاربر"""
    user = request.user
    guest_reservations = GuestReservation.objects.filter(host_user=user).order_by('-reservation_date')
    
    # فیلتر بر اساس تاریخ
    date = request.query_params.get('date')
    if date:
        parsed_date = parse_date_filter(date)
        if parsed_date:
            guest_reservations = guest_reservations.filter(daily_menu__date=parsed_date)
    
    # فیلتر بر اساس وضعیت
    status_filter = request.query_params.get('status')
    if status_filter:
        guest_reservations = guest_reservations.filter(status=status_filter)
    
    serializer = SimpleGuestReservationSerializer(guest_reservations, many=True)
    return Response(serializer.data)


@extend_schema(
    operation_id='user_reservations_summary',
    summary='Get User Reservations Summary',
    description='Get summary of user reservations and guest reservations',
    tags=['User Reservations']
)
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def user_reservations_summary(request):
    """خلاصه رزروهای کاربر"""
    user = request.user
    
    # رزروهای شخصی
    personal_reservations = FoodReservation.objects.filter(user=user)
    personal_count = personal_reservations.count()
    personal_reserved = personal_reservations.filter(status='reserved').count()
    personal_cancelled = personal_reservations.filter(status='cancelled').count()
    personal_served = personal_reservations.filter(status='served').count()
    
    # رزروهای مهمان
    guest_reservations = GuestReservation.objects.filter(host_user=user)
    guest_count = guest_reservations.count()
    guest_reserved = guest_reservations.filter(status='reserved').count()
    guest_cancelled = guest_reservations.filter(status='cancelled').count()
    guest_served = guest_reservations.filter(status='served').count()
    
    # رزروهای امروز
    today = timezone.now().date()
    today_personal = personal_reservations.filter(daily_menu__date=today).count()
    today_guest = guest_reservations.filter(daily_menu__date=today).count()
    
    return Response({
        'personal_reservations': {
            'total': personal_count,
            'reserved': personal_reserved,
            'cancelled': personal_cancelled,
            'served': personal_served,
            'today': today_personal
        },
        'guest_reservations': {
            'total': guest_count,
            'reserved': guest_reserved,
            'cancelled': guest_cancelled,
            'served': guest_served,
            'today': today_guest
        },
        'total_today': today_personal + today_guest,
        'total_all': personal_count + guest_count
    })


# ========== Employee Menu and Reservation Management ==========

@extend_schema(
    operation_id='employee_daily_menus',
    summary='Get Daily Menus for Employee',
    description='Get daily menus for the employee\'s center on a specific date',
    tags=['Employee Management']
)
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def employee_daily_menus(request):
    """منوهای روزانه برای کارمند"""
    user = request.user
    
    # بررسی اینکه کاربر مرکز دارد
    if not user.center:
        return Response(
            {'error': 'کاربر مرکز مشخصی ندارد'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # دریافت تاریخ از query parameter
    date = request.query_params.get('date')
    if not date:
        return Response(
            {'error': 'تاریخ الزامی است'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # تبدیل تاریخ شمسی یا میلادی به فرمت مناسب
    parsed_date = parse_date_filter(date)
    if not parsed_date:
        return Response(
            {'error': 'فرمت تاریخ نامعتبر است. از فرمت میلادی (2025-10-24) یا شمسی (1404/08/02) استفاده کنید'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # دریافت منوهای روزانه برای مرکز کاربر در تاریخ مشخص
    daily_menus = DailyMenu.objects.filter(
        weekly_menu__center=user.center,
        date=parsed_date,
        is_available=True
    ).select_related('meal_type', 'weekly_menu__center').prefetch_related('meals')
    
    serializer = DailyMenuSerializer(daily_menus, many=True)
    return Response(serializer.data)


@extend_schema(
    operation_id='employee_reservations',
    summary='Employee Reservations',
    description='Get all reservations for the authenticated employee or create a new reservation',
    tags=['Employee Management']
)
@api_view(['GET', 'POST'])
@permission_classes([permissions.IsAuthenticated])
def employee_reservations(request):
    """رزروهای کارمند"""
    user = request.user
    
    # بررسی اینکه کاربر مرکز دارد
    if not user.center:
        return Response(
            {'error': 'کاربر مرکز مشخصی ندارد'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if request.method == 'GET':
        # لیست رزروها
        reservations = FoodReservation.objects.filter(user=user).order_by('-reservation_date')
        
        # فیلتر بر اساس تاریخ
        date = request.query_params.get('date')
        if date:
            parsed_date = parse_date_filter(date)
            if parsed_date:
                reservations = reservations.filter(daily_menu__date=parsed_date)
        
        # فیلتر بر اساس وضعیت
        status_filter = request.query_params.get('status')
        if status_filter:
            reservations = reservations.filter(status=status_filter)
        
        serializer = SimpleFoodReservationSerializer(reservations, many=True)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        # ایجاد رزرو جدید
        serializer = FoodReservationCreateSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            # بررسی اینکه daily_menu متعلق به مرکز کاربر است
            daily_menu = serializer.validated_data['daily_menu']
            if daily_menu.weekly_menu.center != user.center:
                return Response(
                    {'error': 'شما نمی‌توانید برای این مرکز رزرو کنید'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # ایجاد رزرو
            reservation = serializer.save(user=user)
            response_serializer = SimpleFoodReservationSerializer(reservation)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    operation_id='employee_create_guest_reservation',
    summary='Create Guest Reservation (Employee)',
    description='Create a guest reservation for the authenticated employee',
    tags=['Employee Management']
)
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def employee_create_guest_reservation(request):
    """ایجاد رزرو مهمان برای کارمند"""
    user = request.user
    
    # بررسی اینکه کاربر مرکز دارد
    if not user.center:
        return Response(
            {'error': 'کاربر مرکز مشخصی ندارد'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    serializer = GuestReservationCreateSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        # بررسی اینکه daily_menu متعلق به مرکز کاربر است
        daily_menu = serializer.validated_data['daily_menu']
        if daily_menu.weekly_menu.center != user.center:
            return Response(
                {'error': 'شما نمی‌توانید برای این مرکز رزرو کنید'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # ایجاد رزرو مهمان
        guest_reservation = serializer.save(host_user=user)
        response_serializer = SimpleGuestReservationSerializer(guest_reservation)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    operation_id='employee_update_reservation',
    summary='Update Food Reservation (Employee)',
    description='Update a food reservation (only own reservations)',
    tags=['Employee Management']
)
@api_view(['PUT', 'PATCH'])
@permission_classes([permissions.IsAuthenticated])
def employee_update_reservation(request, reservation_id):
    """ویرایش رزرو غذا برای کارمند"""
    user = request.user
    
    try:
        reservation = FoodReservation.objects.get(id=reservation_id, user=user)
    except FoodReservation.DoesNotExist:
        return Response(
            {'error': 'رزرو یافت نشد'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    
    # بررسی اینکه رزرو قابل ویرایش است
    if reservation.status != 'reserved':
        return Response(
            {'error': 'فقط رزروهای فعال قابل ویرایش هستند'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    serializer = FoodReservationCreateSerializer(
        reservation, 
        data=request.data, 
        partial=request.method == 'PATCH',
        context={'request': request}
    )
    
    if serializer.is_valid():
        # بررسی اینکه daily_menu متعلق به مرکز کاربر است
        daily_menu = serializer.validated_data['daily_menu']
        if daily_menu.weekly_menu.center != user.center:
            return Response(
                {'error': 'شما نمی‌توانید برای این مرکز رزرو کنید'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer.save()
        response_serializer = SimpleFoodReservationSerializer(reservation)
        return Response(response_serializer.data)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    operation_id='employee_update_guest_reservation',
    summary='Update Guest Reservation (Employee)',
    description='Update a guest reservation (only own guest reservations)',
    tags=['Employee Management']
)
@api_view(['PUT', 'PATCH'])
@permission_classes([permissions.IsAuthenticated])
def employee_update_guest_reservation(request, guest_reservation_id):
    """ویرایش رزرو مهمان برای کارمند"""
    user = request.user
    
    try:
        guest_reservation = GuestReservation.objects.get(id=guest_reservation_id, host_user=user)
    except GuestReservation.DoesNotExist:
        return Response(
            {'error': 'رزرو مهمان یافت نشد'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    
    # بررسی اینکه رزرو قابل ویرایش است
    if guest_reservation.status != 'reserved':
        return Response(
            {'error': 'فقط رزروهای فعال قابل ویرایش هستند'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    serializer = GuestReservationCreateSerializer(
        guest_reservation, 
        data=request.data, 
        partial=request.method == 'PATCH',
        context={'request': request}
    )
    
    if serializer.is_valid():
        # بررسی اینکه daily_menu متعلق به مرکز کاربر است
        daily_menu = serializer.validated_data['daily_menu']
        if daily_menu.weekly_menu.center != user.center:
            return Response(
                {'error': 'شما نمی‌توانید برای این مرکز رزرو کنید'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer.save()
        response_serializer = SimpleGuestReservationSerializer(guest_reservation)
        return Response(response_serializer.data)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    operation_id='employee_cancel_reservation',
    summary='Cancel Food Reservation (Employee)',
    description='Cancel a food reservation (only own reservations)',
    tags=['Employee Management']
)
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def employee_cancel_reservation(request, reservation_id):
    """لغو رزرو غذا برای کارمند"""
    user = request.user
    
    try:
        reservation = FoodReservation.objects.get(id=reservation_id, user=user)
    except FoodReservation.DoesNotExist:
        return Response(
            {'error': 'رزرو یافت نشد'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    
    if reservation.cancel():
        response_serializer = SimpleFoodReservationSerializer(reservation)
        return Response(response_serializer.data)
    else:
        return Response(
            {'error': 'رزرو قابل لغو نیست'}, 
            status=status.HTTP_400_BAD_REQUEST
        )


@extend_schema(
    operation_id='employee_cancel_guest_reservation',
    summary='Cancel Guest Reservation (Employee)',
    description='Cancel a guest reservation (only own guest reservations)',
    tags=['Employee Management']
)
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def employee_cancel_guest_reservation(request, guest_reservation_id):
    """لغو رزرو مهمان برای کارمند"""
    user = request.user
    
    try:
        guest_reservation = GuestReservation.objects.get(id=guest_reservation_id, host_user=user)
    except GuestReservation.DoesNotExist:
        return Response(
            {'error': 'رزرو مهمان یافت نشد'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    
    if guest_reservation.cancel():
        response_serializer = SimpleGuestReservationSerializer(guest_reservation)
        return Response(response_serializer.data)
    else:
        return Response(
            {'error': 'رزرو مهمان قابل لغو نیست'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
