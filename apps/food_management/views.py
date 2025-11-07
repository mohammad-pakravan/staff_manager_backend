from rest_framework import generics, status, permissions
from .permissions import (
    IsFoodAdminOrSystemAdmin,
    IsFoodAdminSystemAdminOrEmployee,
    FoodManagementPermission,
    StatisticsPermission
)
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
    BaseMeal, MealOption, DailyMenu, 
    FoodReservation, FoodReport, GuestReservation
)
# برای سازگاری با کدهای قبلی
Meal = BaseMeal
from apps.centers.models import Center
from .serializers import (
    RestaurantSerializer, MealSerializer,
    DailyMenuSerializer, FoodReservationSerializer,
    FoodReservationCreateSerializer, FoodReportSerializer,
    MealStatisticsSerializer,
    GuestReservationSerializer, GuestReservationCreateSerializer,
    SimpleFoodReservationSerializer, SimpleGuestReservationSerializer,
    MealOptionReportSerializer, BaseMealReportSerializer, UserReportSerializer,
    DateReportSerializer, DetailedReservationReportSerializer, ComprehensiveReportSerializer,
    MealOptionSerializer
)
from .models import Restaurant


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
        tags=['Meals'],
        request=MealSerializer,
        responses={
            201: MealSerializer,
            400: {'description': 'Validation error'},
            403: {'description': 'Permission denied'}
        }
    )
)
class MealListCreateView(generics.ListCreateAPIView):
    """لیست و ایجاد غذاها"""
    queryset = Meal.objects.all()
    serializer_class = MealSerializer
    permission_classes = [FoodManagementPermission]
    pagination_class = CustomPageNumberPagination

    def get_queryset(self):
        # ادمین سیستم و ادمین غذا می‌توانند همه غذاها را ببینند
        # کاربران عادی فقط غذاهای مرکز خود را می‌بینند
        user = self.request.user
        if user.role in ['sys_admin', 'admin_food']:
            return Meal.objects.all()
        elif user.centers.exists():
            return Meal.objects.filter(is_active=True, center__in=user.centers.all())
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
        tags=['Meals'],
        request=MealSerializer,
        responses={
            200: MealSerializer,
            400: {'description': 'Validation error'},
            403: {'description': 'Permission denied'},
            404: {'description': 'Meal not found'}
        }
    ),
    patch=extend_schema(
        operation_id='meal_partial_update',
        summary='Partial Update Meal',
        description='Partially update meal (only for admins)',
        tags=['Meals'],
        request=MealSerializer,
        responses={
            200: MealSerializer,
            400: {'description': 'Validation error'},
            403: {'description': 'Permission denied'},
            404: {'description': 'Meal not found'}
        }
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
    permission_classes = [FoodManagementPermission]

    def get_queryset(self):
        user = self.request.user
        if user.role in ['admin_food', 'sys_admin']:
            return Meal.objects.all()
        # کاربران عادی فقط غذاهای مرکز خود را می‌بینند
        elif user.centers.exists():
            return Meal.objects.filter(center__in=user.centers.all())
        else:
            return Meal.objects.none()


# ========== Meal Type Management ==========


# ========== Restaurant Management ==========

@extend_schema_view(
    get=extend_schema(
        operation_id='restaurant_list',
        summary='List Restaurants',
        description='Get list of all restaurants. Admins see all restaurants, employees see only their center restaurants.',
        tags=['Food Management'],
        responses={200: RestaurantSerializer(many=True)}
    ),
    post=extend_schema(
        operation_id='restaurant_create',
        summary='Create Restaurant',
        description='Create a new restaurant for a center (Admin only)',
        tags=['Food Management'],
        request=RestaurantSerializer,
        responses={
            201: RestaurantSerializer,
            400: {'description': 'Validation error'},
            403: {'description': 'Permission denied'}
        }
    )
)
class RestaurantListCreateView(generics.ListCreateAPIView):
    """لیست و ایجاد رستوران‌ها"""
    serializer_class = RestaurantSerializer
    permission_classes = [FoodManagementPermission]

    def get_queryset(self):
        user = self.request.user
        if user.is_admin:
            return Restaurant.objects.all()
        # Employees see only their centers' restaurants
        if user.centers.exists():
            return Restaurant.objects.filter(center__in=user.centers.all(), is_active=True)
        return Restaurant.objects.none()

    def perform_create(self, serializer):
        serializer.save()


# ========== Meal Option Management ==========

@extend_schema_view(
    get=extend_schema(
        operation_id='meal_option_list',
        summary='List Meal Options',
        description='Get list of all meal options. Admins see all, employees see only their center meal options.',
        tags=['Food Management']
    ),
    post=extend_schema(
        operation_id='meal_option_create',
        summary='Create Meal Option',
        description='Create a new meal option for a base meal (Food Admin only)',
        tags=['Food Management'],
        request=MealOptionSerializer,
        responses={
            201: MealOptionSerializer,
            400: {'description': 'Validation error'},
            403: {'description': 'Permission denied'}
        }
    )
)
class MealOptionListCreateView(generics.ListCreateAPIView):
    """لیست و ایجاد اپشن غذا"""
    serializer_class = MealOptionSerializer
    permission_classes = [FoodManagementPermission]
    pagination_class = CustomPageNumberPagination

    def list(self, request, *args, **kwargs):
        base_meal_id = request.query_params.get('base_meal')
        
        # اگر base_meal مشخص شده، response متفاوت بده
        if base_meal_id:
            try:
                base_meal = BaseMeal.objects.select_related('center', 'restaurant').get(pk=base_meal_id)
                
                # بررسی دسترسی
                user = request.user
                if not user.is_admin and user.centers.exists():
                    if not user.has_center(base_meal.center):
                        return Response(
                            {'error': 'شما به این غذا دسترسی ندارید'},
                            status=status.HTTP_403_FORBIDDEN
                        )
                
                # دریافت MealOptions
                meal_options = base_meal.options.filter(is_active=True).order_by('sort_order', 'title')
                
                # ساخت response - اطلاعات BaseMeal یکبار و options بدون اطلاعات تکراری
                from .serializers import BaseMealSerializer, MealOptionInBaseMealSerializer
                
                # ساخت serializer برای BaseMeal بدون options (چون options را جداگانه می‌فرستیم)
                base_meal_data = BaseMealSerializer(base_meal, context={'request': request}).data
                # حذف options از base_meal_data چون جداگانه می‌فرستیم
                base_meal_data.pop('options', None)
                
                options_data = MealOptionInBaseMealSerializer(meal_options, many=True, context={'request': request}).data
                
                return Response({
                    'base_meal': base_meal_data,
                    'options': options_data
                })
            except BaseMeal.DoesNotExist:
                return Response(
                    {'error': 'غذای پایه یافت نشد'},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        # حالت عادی - لیست تخت MealOptions
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        user = self.request.user
        base_meal_id = self.request.query_params.get('base_meal')
        
        queryset = MealOption.objects.select_related('base_meal', 'base_meal__center', 'base_meal__restaurant')
        
        # فیلتر بر اساس base_meal
        if base_meal_id:
            queryset = queryset.filter(base_meal_id=base_meal_id)
        
        if user.is_admin:
            return queryset.all()
        # Employees see only their center's meal options
        if user.centers.exists():
            return queryset.filter(base_meal__center__in=user.centers.all(), is_active=True)
        return queryset.none()

    def perform_create(self, serializer):
        # فقط ادمین‌های غذا و سیستم می‌توانند اپشن غذا ایجاد کنند
        user = self.request.user
        if user.role not in ['admin_food', 'sys_admin']:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("فقط ادمین‌های غذا می‌توانند اپشن غذا ایجاد کنند")
        
        serializer.save()


@extend_schema_view(
    get=extend_schema(
        operation_id='meal_option_detail',
        summary='Get Meal Option Details',
        description='Get details of a specific meal option',
        tags=['Food Management']
    ),
    put=extend_schema(
        operation_id='meal_option_update',
        summary='Update Meal Option',
        description='Update meal option completely (Food Admin only)',
        tags=['Food Management'],
        request=MealOptionSerializer,
        responses={
            200: MealOptionSerializer,
            400: {'description': 'Validation error'},
            403: {'description': 'Permission denied'},
            404: {'description': 'Meal option not found'}
        }
    ),
    patch=extend_schema(
        operation_id='meal_option_partial_update',
        summary='Partial Update Meal Option',
        description='Partially update meal option (Food Admin only)',
        tags=['Food Management'],
        request=MealOptionSerializer,
        responses={
            200: MealOptionSerializer,
            400: {'description': 'Validation error'},
            403: {'description': 'Permission denied'},
            404: {'description': 'Meal option not found'}
        }
    ),
    delete=extend_schema(
        operation_id='meal_option_delete',
        summary='Delete Meal Option',
        description='Delete meal option (Food Admin only)',
        tags=['Food Management']
    )
)
class MealOptionDetailView(generics.RetrieveUpdateDestroyAPIView):
    """جزئیات، ویرایش و حذف اپشن غذا"""
    serializer_class = MealOptionSerializer
    permission_classes = [FoodManagementPermission]

    def get_queryset(self):
        user = self.request.user
        if user.is_admin:
            return MealOption.objects.all()
        # کاربران عادی فقط اپشن‌های مرکز خود را می‌بینند
        elif user.centers.exists():
            return MealOption.objects.filter(base_meal__center__in=user.centers.all())
        else:
            return MealOption.objects.none()

    def perform_update(self, serializer):
        # فقط ادمین‌های غذا و سیستم می‌توانند اپشن غذا ویرایش کنند
        user = self.request.user
        if user.role not in ['admin_food', 'sys_admin']:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("فقط ادمین‌های غذا می‌توانند اپشن غذا ویرایش کنند")
        serializer.save()

    def perform_destroy(self, instance):
        # فقط ادمین‌های غذا و سیستم می‌توانند اپشن غذا حذف کنند
        user = self.request.user
        if user.role not in ['admin_food', 'sys_admin']:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("فقط ادمین‌های غذا می‌توانند اپشن غذا حذف کنند")
        instance.delete()


@extend_schema_view(
    get=extend_schema(
        operation_id='restaurant_detail',
        summary='Get Restaurant Details',
        description='Get details of a specific restaurant',
        tags=['Food Management']
    ),
    put=extend_schema(
        operation_id='restaurant_update',
        summary='Update Restaurant',
        description='Update restaurant completely (Food Admin & System Admin only)',
        tags=['Food Management'],
        request=RestaurantSerializer,
        responses={
            200: RestaurantSerializer,
            400: {'description': 'Validation error'},
            403: {'description': 'Permission denied'},
            404: {'description': 'Restaurant not found'}
        }
    ),
    patch=extend_schema(
        operation_id='restaurant_partial_update',
        summary='Partial Update Restaurant',
        description='Partially update restaurant (Food Admin & System Admin only)',
        tags=['Food Management'],
        request=RestaurantSerializer,
        responses={
            200: RestaurantSerializer,
            400: {'description': 'Validation error'},
            403: {'description': 'Permission denied'},
            404: {'description': 'Restaurant not found'}
        }
    ),
    delete=extend_schema(
        operation_id='restaurant_delete',
        summary='Delete Restaurant',
        description='Delete restaurant (Food Admin & System Admin only)',
        tags=['Food Management']
    )
)
class RestaurantDetailView(generics.RetrieveUpdateDestroyAPIView):
    """جزئیات رستوران"""
    serializer_class = RestaurantSerializer
    permission_classes = [FoodManagementPermission]

    def get_queryset(self):
        user = self.request.user
        if user.is_admin:
            return Restaurant.objects.all()
        # Employees see only their centers' restaurants
        if user.centers.exists():
            return Restaurant.objects.filter(center__in=user.centers.all(), is_active=True)
        return Restaurant.objects.none()


# ========== Weekly Menu Management ==========

# ========== Daily Menu Views ==========

class DailyMenuListView(generics.ListAPIView):
    """لیست منوهای روزانه"""
    serializer_class = DailyMenuSerializer
    permission_classes = [FoodManagementPermission]

    def get_queryset(self):
        user = self.request.user
        center_id = self.request.query_params.get('center')
        date = self.request.query_params.get('date')
        
        queryset = DailyMenu.objects.filter(is_available=True)
        
        # فیلتر بر اساس مرکز
        if center_id:
            try:
                center_id = int(center_id)
                queryset = queryset.filter(center_id=center_id)
            except (ValueError, TypeError):
                # Invalid center_id, return empty queryset
                queryset = queryset.none()
        elif user.centers.exists() and not user.is_admin:
            queryset = queryset.filter(center__in=user.centers.all())
        
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
        
        return queryset.order_by('date')


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
        tags=['Reservations'],
        request=FoodReservationCreateSerializer,
        responses={
            201: SimpleFoodReservationSerializer,
            400: {'description': 'Validation error'},
            403: {'description': 'Permission denied'}
        }
    )
)
class FoodReservationListCreateView(generics.ListCreateAPIView):
    """لیست و ایجاد رزروهای غذا"""
    permission_classes = [FoodManagementPermission]
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
    permission_classes = [FoodManagementPermission]

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
@permission_classes([FoodManagementPermission])
def user_reservation_limits(request):
    """بررسی محدودیت‌های رزرو کاربر - محدودیت رزرو برداشته شده است"""
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
    
    return Response({
        'user': {
            'id': user.id,
            'username': user.username,
            'full_name': f"{user.first_name} {user.last_name}".strip(),
        },
        'date': date,
        'current_reservations': current_reservations,
        'unlimited': True,  # محدودیت برداشته شده است
        'can_reserve': True  # همیشه می‌تواند رزرو کند
    })


@api_view(['POST'])
@permission_classes([FoodManagementPermission])
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
    permission_classes = [FoodManagementPermission]
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
    permission_classes = [FoodManagementPermission]

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
@permission_classes([FoodManagementPermission])
def user_guest_reservation_limits(request):
    """بررسی محدودیت‌های رزرو مهمان کاربر - محدودیت رزرو برداشته شده است"""
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
    
    return Response({
        'user': {
            'id': user.id,
            'username': user.username,
            'full_name': f"{user.first_name} {user.last_name}".strip(),
        },
        'date': date,
        'current_guest_reservations': current_guest_reservations,
        'unlimited': True,  # محدودیت برداشته شده است
        'can_reserve_guest': True  # همیشه می‌تواند رزرو کند
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
@permission_classes([FoodManagementPermission])
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

@extend_schema(
    operation_id='comprehensive_statistics',
    summary='Comprehensive Statistics',
    description='Get comprehensive statistics with filters by date, center, and user',
    tags=['Statistics'],
    parameters=[
        {
            'name': 'center_id',
            'in': 'query',
            'description': 'فیلتر بر اساس مرکز',
            'required': False,
            'schema': {'type': 'integer'}
        },
        {
            'name': 'user_id',
            'in': 'query',
            'description': 'فیلتر بر اساس کاربر',
            'required': False,
            'schema': {'type': 'integer'}
        },
        {
            'name': 'start_date',
            'in': 'query',
            'description': 'تاریخ شروع (فرمت: YYYY-MM-DD یا YYYY/MM/DD)',
            'required': False,
            'schema': {'type': 'string'}
        },
        {
            'name': 'end_date',
            'in': 'query',
            'description': 'تاریخ پایان (فرمت: YYYY-MM-DD یا YYYY/MM/DD)',
            'required': False,
            'schema': {'type': 'string'}
        },
    ]
)
@api_view(['GET'])
@permission_classes([StatisticsPermission])
def comprehensive_statistics(request):
    """آمار جامع با امکان فیلتر"""
    user = request.user
    
    # اگر کاربر ادمین نیست، فقط آمار مراکز خودش را ببیند
    if not user.is_admin:
        if not user.centers.exists():
            return Response({
                'error': 'کاربر مرکز مشخصی ندارد'
            }, status=status.HTTP_403_FORBIDDEN)
    
    # دریافت فیلترها
    center_id = request.query_params.get('center_id')
    user_id = request.query_params.get('user_id')
    start_date = parse_date_filter(request.query_params.get('start_date'))
    end_date = parse_date_filter(request.query_params.get('end_date'))
    
    # ساخت queryset های پایه
    base_meals_qs = BaseMeal.objects.all()
    meal_options_qs = MealOption.objects.all()
    restaurants_qs = Restaurant.objects.all()
    from apps.accounts.models import User
    users_qs = User.objects.all()
    reservations_qs = FoodReservation.objects.all()
    guest_reservations_qs = GuestReservation.objects.all()
    daily_menus_qs = DailyMenu.objects.all()
    centers_qs = Center.objects.all()
    
    # فیلتر بر اساس مرکز
    if center_id:
        base_meals_qs = base_meals_qs.filter(center_id=center_id)
        meal_options_qs = meal_options_qs.filter(base_meal__center_id=center_id)
        restaurants_qs = restaurants_qs.filter(center_id=center_id)
        users_qs = users_qs.filter(centers__id=center_id).distinct()
        reservations_qs = reservations_qs.filter(daily_menu__center_id=center_id)
        guest_reservations_qs = guest_reservations_qs.filter(daily_menu__center_id=center_id)
        daily_menus_qs = daily_menus_qs.filter(center_id=center_id)
        centers_qs = centers_qs.filter(id=center_id)
    elif not user.is_admin:
        # اگر ادمین نیست، فقط مراکز خودش
        user_centers = user.centers.all()
        if user_centers.exists():
            base_meals_qs = base_meals_qs.filter(center__in=user_centers)
            meal_options_qs = meal_options_qs.filter(base_meal__center__in=user_centers)
            restaurants_qs = restaurants_qs.filter(center__in=user_centers)
            users_qs = users_qs.filter(centers__in=user_centers).distinct()
            reservations_qs = reservations_qs.filter(daily_menu__center__in=user_centers)
            guest_reservations_qs = guest_reservations_qs.filter(daily_menu__center__in=user_centers)
            daily_menus_qs = daily_menus_qs.filter(center__in=user_centers)
            centers_qs = centers_qs.filter(id__in=user_centers.values_list('id', flat=True))
        else:
            centers_qs = Center.objects.none()
    
    # فیلتر بر اساس کاربر
    if user_id:
        reservations_qs = reservations_qs.filter(user_id=user_id)
        guest_reservations_qs = guest_reservations_qs.filter(host_user_id=user_id)
    
    # فیلتر بر اساس تاریخ
    if start_date:
        reservations_qs = reservations_qs.filter(daily_menu__date__gte=start_date)
        guest_reservations_qs = guest_reservations_qs.filter(daily_menu__date__gte=start_date)
        daily_menus_qs = daily_menus_qs.filter(date__gte=start_date)
    
    if end_date:
        reservations_qs = reservations_qs.filter(daily_menu__date__lte=end_date)
        guest_reservations_qs = guest_reservations_qs.filter(daily_menu__date__lte=end_date)
        daily_menus_qs = daily_menus_qs.filter(date__lte=end_date)
    
    # محاسبه آمار
    from decimal import Decimal
    today = timezone.now().date()
    
    # آمار غذاها
    total_base_meals = base_meals_qs.count()
    active_base_meals = base_meals_qs.filter(is_active=True).count()
    base_meal_ids = {
        'all': list(base_meals_qs.values_list('id', flat=True)),
        'active': list(base_meals_qs.filter(is_active=True).values_list('id', flat=True)),
        'inactive': list(base_meals_qs.filter(is_active=False).values_list('id', flat=True))
    }
    
    # آمار اپشن‌ها
    total_meal_options = meal_options_qs.count()
    active_meal_options = meal_options_qs.filter(is_active=True).count()
    meal_option_ids = {
        'all': list(meal_options_qs.values_list('id', flat=True)),
        'active': list(meal_options_qs.filter(is_active=True).values_list('id', flat=True)),
        'inactive': list(meal_options_qs.filter(is_active=False).values_list('id', flat=True))
    }
    
    # آمار رستوران‌ها
    total_restaurants = restaurants_qs.count()
    active_restaurants = restaurants_qs.filter(is_active=True).count()
    restaurant_ids = {
        'all': list(restaurants_qs.values_list('id', flat=True)),
        'active': list(restaurants_qs.filter(is_active=True).values_list('id', flat=True)),
        'inactive': list(restaurants_qs.filter(is_active=False).values_list('id', flat=True))
    }
    
    # آمار کاربران
    total_users = users_qs.count()
    active_users = users_qs.filter(is_active=True).count()
    user_ids = {
        'all': list(users_qs.values_list('id', flat=True)),
        'active': list(users_qs.filter(is_active=True).values_list('id', flat=True)),
        'inactive': list(users_qs.filter(is_active=False).values_list('id', flat=True))
    }
    
    # آمار منوهای روزانه
    total_daily_menus = daily_menus_qs.count()
    active_daily_menus = daily_menus_qs.filter(is_available=True).count()
    daily_menu_ids = {
        'all': list(daily_menus_qs.values_list('id', flat=True)),
        'active': list(daily_menus_qs.filter(is_available=True).values_list('id', flat=True)),
        'inactive': list(daily_menus_qs.filter(is_available=False).values_list('id', flat=True))
    }
    
    # آمار رزروها
    total_reservations = reservations_qs.count()
    reserved_reservations = reservations_qs.filter(status='reserved').count()
    cancelled_reservations = reservations_qs.filter(status='cancelled').count()
    served_reservations = reservations_qs.filter(status='served').count()
    today_reservations = reservations_qs.filter(daily_menu__date=today).count()
    
    # لیست ID های رزروها
    reservation_ids = {
        'all': list(reservations_qs.values_list('id', flat=True)),
        'reserved': list(reservations_qs.filter(status='reserved').values_list('id', flat=True)),
        'cancelled': list(reservations_qs.filter(status='cancelled').values_list('id', flat=True)),
        'served': list(reservations_qs.filter(status='served').values_list('id', flat=True)),
        'today': list(reservations_qs.filter(daily_menu__date=today).values_list('id', flat=True))
    }
    
    # آمار رزروهای مهمان
    total_guest_reservations = guest_reservations_qs.count()
    reserved_guest_reservations = guest_reservations_qs.filter(status='reserved').count()
    cancelled_guest_reservations = guest_reservations_qs.filter(status='cancelled').count()
    served_guest_reservations = guest_reservations_qs.filter(status='served').count()
    today_guest_reservations = guest_reservations_qs.filter(daily_menu__date=today).count()
    
    # لیست ID های رزروهای مهمان
    guest_reservation_ids = {
        'all': list(guest_reservations_qs.values_list('id', flat=True)),
        'reserved': list(guest_reservations_qs.filter(status='reserved').values_list('id', flat=True)),
        'cancelled': list(guest_reservations_qs.filter(status='cancelled').values_list('id', flat=True)),
        'served': list(guest_reservations_qs.filter(status='served').values_list('id', flat=True)),
        'today': list(guest_reservations_qs.filter(daily_menu__date=today).values_list('id', flat=True))
    }
    
    # محاسبه مبالغ
    total_amount = Decimal('0')
    reserved_amount = Decimal('0')
    served_amount = Decimal('0')
    cancelled_amount = Decimal('0')
    
    for reservation in reservations_qs.select_related('meal_option'):
        amount = Decimal(str(reservation.amount or 0)) * Decimal(str(reservation.quantity or 1))
        total_amount += amount
        if reservation.status == 'reserved':
            reserved_amount += amount
        elif reservation.status == 'served':
            served_amount += amount
        elif reservation.status == 'cancelled':
            cancelled_amount += amount
    
    for guest_reservation in guest_reservations_qs.select_related('meal_option'):
        amount = Decimal(str(guest_reservation.amount or 0))
        total_amount += amount
        if guest_reservation.status == 'reserved':
            reserved_amount += amount
        elif guest_reservation.status == 'served':
            served_amount += amount
        elif guest_reservation.status == 'cancelled':
            cancelled_amount += amount
    
    # آمار مجموع
    total_all_reservations = total_reservations + total_guest_reservations
    total_today_reservations = today_reservations + today_guest_reservations
    
    # آمار مراکز
    total_centers = centers_qs.count()
    center_ids = {
        'all': list(centers_qs.values_list('id', flat=True))
    }
    
    # ساخت response
    stats = {
        'base_meals': {
            'total': total_base_meals,
            'active': active_base_meals,
            'inactive': total_base_meals - active_base_meals,
            'ids': base_meal_ids
        },
        'meal_options': {
            'total': total_meal_options,
            'active': active_meal_options,
            'inactive': total_meal_options - active_meal_options,
            'ids': meal_option_ids
        },
        'restaurants': {
            'total': total_restaurants,
            'active': active_restaurants,
            'inactive': total_restaurants - active_restaurants,
            'ids': restaurant_ids
        },
        'users': {
            'total': total_users,
            'active': active_users,
            'inactive': total_users - active_users,
            'ids': user_ids
        },
        'centers': {
            'total': total_centers,
            'ids': center_ids
        },
        'daily_menus': {
            'total': total_daily_menus,
            'active': active_daily_menus,
            'inactive': total_daily_menus - active_daily_menus,
            'ids': daily_menu_ids
        },
        'reservations': {
            'total': total_reservations,
            'reserved': reserved_reservations,
            'cancelled': cancelled_reservations,
            'served': served_reservations,
            'today': today_reservations,
            'ids': reservation_ids
        },
        'guest_reservations': {
            'total': total_guest_reservations,
            'reserved': reserved_guest_reservations,
            'cancelled': cancelled_guest_reservations,
            'served': served_guest_reservations,
            'today': today_guest_reservations,
            'ids': guest_reservation_ids
        },
        'summary': {
            'total_reservations': total_all_reservations,
            'total_today_reservations': total_today_reservations,
            'total_amount': str(total_amount),
            'reserved_amount': str(reserved_amount),
            'served_amount': str(served_amount),
            'cancelled_amount': str(cancelled_amount)
        },
        'filters': {
            'center_id': int(center_id) if center_id else None,
            'user_id': int(user_id) if user_id else None,
            'start_date': start_date.isoformat() if start_date else None,
            'end_date': end_date.isoformat() if end_date else None
        }
    }
    
    return Response(stats)


@api_view(['GET'])
@permission_classes([StatisticsPermission])
def meal_statistics(request):
    """آمار کلی غذاها (برای سازگاری با کدهای قبلی)"""
    return comprehensive_statistics(request)


@api_view(['GET'])
@permission_classes([IsFoodAdminOrSystemAdmin])
def center_reservations(request, center_id):
    """رزروهای یک مرکز خاص"""
    if not request.user.is_admin:
        return Response({
            'error': 'دسترسی غیرمجاز'
        }, status=status.HTTP_403_FORBIDDEN)
    
    center = get_object_or_404(Center, id=center_id)
    date = request.query_params.get('date')
    
    queryset = FoodReservation.objects.filter(
        daily_menu__center=center
    )
    
    if date:
        parsed_date = parse_date_filter(date)
        if parsed_date:
            queryset = queryset.filter(daily_menu__date=parsed_date)
    
    serializer = SimpleFoodReservationSerializer(queryset, many=True)
    return Response(serializer.data)


# ========== Export Functions ==========

@api_view(['GET'])
@permission_classes([IsFoodAdminOrSystemAdmin])
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
        daily_menu__center=center
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
        ws.cell(row=row, column=3, value='-')
        if reservation.meal_option:
            meal_title = f"{reservation.meal_option.base_meal.title} - {reservation.meal_option.title}"
        else:
            meal_title = 'نامشخص'
        ws.cell(row=row, column=4, value=meal_title)
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
@permission_classes([IsFoodAdminOrSystemAdmin])
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
        daily_menu__center=center
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
            '-',
            f"{reservation.meal_option.base_meal.title} - {reservation.meal_option.title}" if reservation.meal_option else 'نامشخص',
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
@permission_classes([FoodManagementPermission])
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
@permission_classes([FoodManagementPermission])
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
@permission_classes([FoodManagementPermission])
def user_reservations_summary(request):
    """خلاصه رزروهای کاربر"""
    user = request.user
    
    # رزروهای شخصی
    personal_reservations = FoodReservation.objects.filter(user=user)
    personal_count = personal_reservations.count()
    personal_reserved = personal_reservations.filter(status='reserved').count()
    personal_cancelled = personal_reservations.filter(status='cancelled').count()
    personal_served = personal_reservations.filter(status='served').count()
    
    # ID های رزروهای شخصی
    personal_reserved_ids = list(personal_reservations.filter(status='reserved').values_list('id', flat=True))
    personal_cancelled_ids = list(personal_reservations.filter(status='cancelled').values_list('id', flat=True))
    personal_served_ids = list(personal_reservations.filter(status='served').values_list('id', flat=True))
    personal_all_ids = list(personal_reservations.values_list('id', flat=True))
    
    # رزروهای مهمان
    guest_reservations = GuestReservation.objects.filter(host_user=user)
    guest_count = guest_reservations.count()
    guest_reserved = guest_reservations.filter(status='reserved').count()
    guest_cancelled = guest_reservations.filter(status='cancelled').count()
    guest_served = guest_reservations.filter(status='served').count()
    
    # ID های رزروهای مهمان
    guest_reserved_ids = list(guest_reservations.filter(status='reserved').values_list('id', flat=True))
    guest_cancelled_ids = list(guest_reservations.filter(status='cancelled').values_list('id', flat=True))
    guest_served_ids = list(guest_reservations.filter(status='served').values_list('id', flat=True))
    guest_all_ids = list(guest_reservations.values_list('id', flat=True))
    
    # رزروهای امروز
    today = timezone.now().date()
    today_personal = personal_reservations.filter(daily_menu__date=today).count()
    today_guest = guest_reservations.filter(daily_menu__date=today).count()
    today_personal_ids = list(personal_reservations.filter(daily_menu__date=today).values_list('id', flat=True))
    today_guest_ids = list(guest_reservations.filter(daily_menu__date=today).values_list('id', flat=True))
    
    return Response({
        'personal_reservations': {
            'total': personal_count,
            'reserved': personal_reserved,
            'cancelled': personal_cancelled,
            'served': personal_served,
            'today': today_personal,
            'ids': {
                'all': personal_all_ids,
                'reserved': personal_reserved_ids,
                'cancelled': personal_cancelled_ids,
                'served': personal_served_ids,
                'today': today_personal_ids
            }
        },
        'guest_reservations': {
            'total': guest_count,
            'reserved': guest_reserved,
            'cancelled': guest_cancelled,
            'served': guest_served,
            'today': today_guest,
            'ids': {
                'all': guest_all_ids,
                'reserved': guest_reserved_ids,
                'cancelled': guest_cancelled_ids,
                'served': guest_served_ids,
                'today': today_guest_ids
            }
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
@permission_classes([FoodManagementPermission])
def employee_daily_menus(request):
    """منوهای روزانه برای کارمند"""
    user = request.user
    
    # بررسی اینکه کاربر مرکز دارد
    if not user.centers.exists():
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
        center__in=user.centers.all(),
        date=parsed_date,
        is_available=True
    ).select_related('center').prefetch_related('meal_options')
    
    serializer = DailyMenuSerializer(daily_menus, many=True)
    return Response(serializer.data)


@extend_schema(
    operation_id='employee_reservations',
    summary='Employee Reservations',
    description='Get all reservations for the authenticated employee or create a new reservation',
    tags=['Employee Management'],
    request=FoodReservationCreateSerializer,
    responses={
        200: SimpleFoodReservationSerializer(many=True),
        201: SimpleFoodReservationSerializer,
        400: {'description': 'Validation error'},
        403: {'description': 'Permission denied'}
    }
)
@api_view(['GET', 'POST'])
@permission_classes([FoodManagementPermission])
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
            # بررسی اینکه daily_menu متعلق به یکی از مراکز کاربر است
            daily_menu = serializer.validated_data['daily_menu']
            if not user.has_center(daily_menu.center):
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
@permission_classes([FoodManagementPermission])
def employee_create_guest_reservation(request):
    """ایجاد رزرو مهمان برای کارمند"""
    user = request.user
    
    # بررسی اینکه کاربر مرکز دارد
    if not user.centers.exists():
        return Response(
            {'error': 'کاربر مرکز مشخصی ندارد'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    serializer = GuestReservationCreateSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        # بررسی اینکه daily_menu متعلق به یکی از مراکز کاربر است
        daily_menu = serializer.validated_data['daily_menu']
        if not user.has_center(daily_menu.center):
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
    tags=['Employee Management'],
    request=FoodReservationCreateSerializer,
    responses={
        200: SimpleFoodReservationSerializer,
        400: {'description': 'Validation error'},
        403: {'description': 'Permission denied'},
        404: {'description': 'Reservation not found'}
    }
)
@api_view(['PUT', 'PATCH'])
@permission_classes([FoodManagementPermission])
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
        # بررسی اینکه daily_menu متعلق به یکی از مراکز کاربر است
        daily_menu = serializer.validated_data['daily_menu']
        if not user.has_center(daily_menu.center):
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
    tags=['Employee Management'],
    request=GuestReservationCreateSerializer,
    responses={
        200: SimpleGuestReservationSerializer,
        400: {'description': 'Validation error'},
        403: {'description': 'Permission denied'},
        404: {'description': 'Guest reservation not found'}
    }
)
@api_view(['PUT', 'PATCH'])
@permission_classes([FoodManagementPermission])
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
        # بررسی اینکه daily_menu متعلق به یکی از مراکز کاربر است
        daily_menu = serializer.validated_data['daily_menu']
        if not user.has_center(daily_menu.center):
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
@permission_classes([FoodManagementPermission])
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
@permission_classes([FoodManagementPermission])
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


# ========== Report Views ==========

@extend_schema(
    summary='Report by Meal Option',
    description='Complete report of reservations by meal options (MealOption)',
    tags=['Reports'],
    parameters=[
        {
            'name': 'center_id',
            'in': 'query',
            'description': 'فیلتر بر اساس مرکز',
            'required': False,
            'schema': {'type': 'integer'}
        },
        {
            'name': 'start_date',
            'in': 'query',
            'description': 'تاریخ شروع (فرمت: YYYY-MM-DD یا YYYY/MM/DD)',
            'required': False,
            'schema': {'type': 'string'}
        },
        {
            'name': 'end_date',
            'in': 'query',
            'description': 'تاریخ پایان (فرمت: YYYY-MM-DD یا YYYY/MM/DD)',
            'required': False,
            'schema': {'type': 'string'}
        },
    ]
)
@api_view(['GET'])
@permission_classes([StatisticsPermission])
def report_by_meal_option(request):
    """گزارش بر اساس MealOption"""
    if not request.user.is_admin:
        return Response({
            'error': 'دسترسی غیرمجاز'
        }, status=status.HTTP_403_FORBIDDEN)
    
    center_id = request.query_params.get('center_id')
    start_date = parse_date_filter(request.query_params.get('start_date'))
    end_date = parse_date_filter(request.query_params.get('end_date'))
    
    # فیلتر رزروها
    reservations = FoodReservation.objects.all()
    
    if center_id:
        reservations = reservations.filter(daily_menu__center_id=center_id)
    
    if start_date:
        reservations = reservations.filter(daily_menu__date__gte=start_date)
    
    if end_date:
        reservations = reservations.filter(daily_menu__date__lte=end_date)
    
    # گروه‌بندی بر اساس MealOption
    from django.db.models import Sum, Count, Q
    
    meal_options_data = {}
    
    for reservation in reservations.select_related('meal_option', 'meal_option__base_meal', 'meal_option__restaurant', 'daily_menu__center'):
        if not reservation.meal_option:
            continue
        
        meal_option = reservation.meal_option
        meal_option_id = meal_option.id
        
        if meal_option_id not in meal_options_data:
            meal_options_data[meal_option_id] = {
                'meal_option_id': meal_option_id,
                'meal_option_title': meal_option.title,
                'base_meal_title': meal_option.base_meal.title if meal_option.base_meal else '',
                'restaurant_name': meal_option.restaurant.name if meal_option.restaurant else '',
                'restaurant_id': meal_option.restaurant.id if meal_option.restaurant else None,
                'center_name': reservation.daily_menu.center.name if reservation.daily_menu and reservation.daily_menu.center else '',
                'center_id': reservation.daily_menu.center.id if reservation.daily_menu and reservation.daily_menu.center else None,
                'total_reservations': 0,
                'reserved_count': 0,
                'cancelled_count': 0,
                'served_count': 0,
                'total_amount': 0,
                'reserved_amount': 0,
                'served_amount': 0,
            }
        
        data = meal_options_data[meal_option_id]
        data['total_reservations'] += 1
        
        if reservation.status == 'reserved':
            data['reserved_count'] += 1
            data['reserved_amount'] += float(reservation.amount or 0)
        elif reservation.status == 'cancelled':
            data['cancelled_count'] += 1
        elif reservation.status == 'served':
            data['served_count'] += 1
            data['served_amount'] += float(reservation.amount or 0)
        
        data['total_amount'] += float(reservation.amount or 0)
    
    from decimal import Decimal
    for data in meal_options_data.values():
        data['total_amount'] = Decimal(str(data['total_amount']))
        data['reserved_amount'] = Decimal(str(data['reserved_amount']))
        data['served_amount'] = Decimal(str(data['served_amount']))
    
    serializer = MealOptionReportSerializer(list(meal_options_data.values()), many=True)
    return Response(serializer.data)


@extend_schema(
    summary='Report by Base Meal',
    description='Complete report of reservations by base meals',
    tags=['Reports'],
    parameters=[
        {
            'name': 'center_id',
            'in': 'query',
            'description': 'فیلتر بر اساس مرکز',
            'required': False,
            'schema': {'type': 'integer'}
        },
        {
            'name': 'start_date',
            'in': 'query',
            'description': 'تاریخ شروع (فرمت: YYYY-MM-DD یا YYYY/MM/DD)',
            'required': False,
            'schema': {'type': 'string'}
        },
        {
            'name': 'end_date',
            'in': 'query',
            'description': 'تاریخ پایان (فرمت: YYYY-MM-DD یا YYYY/MM/DD)',
            'required': False,
            'schema': {'type': 'string'}
        },
    ]
)
@api_view(['GET'])
@permission_classes([StatisticsPermission])
def report_by_base_meal(request):
    """گزارش بر اساس BaseMeal"""
    if not request.user.is_admin:
        return Response({
            'error': 'دسترسی غیرمجاز'
        }, status=status.HTTP_403_FORBIDDEN)
    
    center_id = request.query_params.get('center_id')
    start_date = parse_date_filter(request.query_params.get('start_date'))
    end_date = parse_date_filter(request.query_params.get('end_date'))
    
    # فیلتر رزروها
    reservations = FoodReservation.objects.select_related(
        'meal_option', 'meal_option__base_meal', 'meal_option__restaurant',
        'daily_menu__center'
    ).filter(meal_option__isnull=False)
    
    if center_id:
        reservations = reservations.filter(daily_menu__center_id=center_id)
    
    if start_date:
        reservations = reservations.filter(daily_menu__date__gte=start_date)
    
    if end_date:
        reservations = reservations.filter(daily_menu__date__lte=end_date)
    
    # گروه‌بندی بر اساس BaseMeal
    base_meals_data = {}
    meal_options_by_base_meal = {}
    
    for reservation in reservations:
        if not reservation.meal_option or not reservation.meal_option.base_meal:
            continue
        
        base_meal = reservation.meal_option.base_meal
        base_meal_id = base_meal.id
        meal_option_id = reservation.meal_option.id
        
        if base_meal_id not in base_meals_data:
            base_meals_data[base_meal_id] = {
                'base_meal_id': base_meal_id,
                'base_meal_title': base_meal.title,
                'restaurant_name': reservation.meal_option.restaurant.name if reservation.meal_option.restaurant else '',
                'center_name': reservation.daily_menu.center.name if reservation.daily_menu and reservation.daily_menu.center else '',
                'meal_options_count': 0,
                'total_reservations': 0,
                'reserved_count': 0,
                'cancelled_count': 0,
                'served_count': 0,
                'total_amount': 0,
            }
            meal_options_by_base_meal[base_meal_id] = {}
        
        data = base_meals_data[base_meal_id]
        data['total_reservations'] += 1
        
        if reservation.status == 'reserved':
            data['reserved_count'] += 1
        elif reservation.status == 'cancelled':
            data['cancelled_count'] += 1
        elif reservation.status == 'served':
            data['served_count'] += 1
        
        data['total_amount'] += float(reservation.amount or 0)
        
        # جمع‌آوری داده‌های MealOption
        if meal_option_id not in meal_options_by_base_meal[base_meal_id]:
            meal_options_by_base_meal[base_meal_id][meal_option_id] = {
                'meal_option_id': meal_option_id,
                'meal_option_title': reservation.meal_option.title,
                'base_meal_title': base_meal.title,
                'restaurant_name': reservation.meal_option.restaurant.name if reservation.meal_option.restaurant else '',
                'restaurant_id': reservation.meal_option.restaurant.id if reservation.meal_option.restaurant else None,
                'center_name': reservation.daily_menu.center.name if reservation.daily_menu and reservation.daily_menu.center else '',
                'center_id': reservation.daily_menu.center.id if reservation.daily_menu and reservation.daily_menu.center else None,
                'total_reservations': 0,
                'reserved_count': 0,
                'cancelled_count': 0,
                'served_count': 0,
                'total_amount': 0,
                'reserved_amount': 0,
                'served_amount': 0,
            }
            data['meal_options_count'] += 1
        
        meal_option_data = meal_options_by_base_meal[base_meal_id][meal_option_id]
        meal_option_data['total_reservations'] += 1
        
        if reservation.status == 'reserved':
            meal_option_data['reserved_count'] += 1
            meal_option_data['reserved_amount'] += float(reservation.amount or 0)
        elif reservation.status == 'cancelled':
            meal_option_data['cancelled_count'] += 1
        elif reservation.status == 'served':
            meal_option_data['served_count'] += 1
            meal_option_data['served_amount'] += float(reservation.amount or 0)
        
        meal_option_data['total_amount'] += float(reservation.amount or 0)
    
    from decimal import Decimal
    result = []
    for base_meal_id, data in base_meals_data.items():
        data['total_amount'] = Decimal(str(data['total_amount']))
        data['meal_options'] = []
        
        for meal_option_data in meal_options_by_base_meal[base_meal_id].values():
            meal_option_data['total_amount'] = Decimal(str(meal_option_data['total_amount']))
            meal_option_data['reserved_amount'] = Decimal(str(meal_option_data['reserved_amount']))
            meal_option_data['served_amount'] = Decimal(str(meal_option_data['served_amount']))
            data['meal_options'].append(meal_option_data)
        
        result.append(data)
    
    serializer = BaseMealReportSerializer(result, many=True)
    return Response(serializer.data)


@extend_schema(
    summary='Report by User',
    description='Complete report of reservations by users',
    tags=['Reports'],
    parameters=[
        {
            'name': 'center_id',
            'in': 'query',
            'description': 'فیلتر بر اساس مرکز',
            'required': False,
            'schema': {'type': 'integer'}
        },
        {
            'name': 'start_date',
            'in': 'query',
            'description': 'تاریخ شروع (فرمت: YYYY-MM-DD یا YYYY/MM/DD)',
            'required': False,
            'schema': {'type': 'string'}
        },
        {
            'name': 'end_date',
            'in': 'query',
            'description': 'تاریخ پایان (فرمت: YYYY-MM-DD یا YYYY/MM/DD)',
            'required': False,
            'schema': {'type': 'string'}
        },
    ]
)
@api_view(['GET'])
@permission_classes([StatisticsPermission])
def report_by_user(request):
    """گزارش بر اساس کاربر"""
    if not request.user.is_admin:
        return Response({
            'error': 'دسترسی غیرمجاز'
        }, status=status.HTTP_403_FORBIDDEN)
    
    center_id = request.query_params.get('center_id')
    start_date = parse_date_filter(request.query_params.get('start_date'))
    end_date = parse_date_filter(request.query_params.get('end_date'))
    
    # فیلتر رزروها
    reservations = FoodReservation.objects.select_related(
        'user', 'user__center', 'daily_menu__center'
    ).all()
    guest_reservations = GuestReservation.objects.select_related(
        'host_user', 'host_user__center', 'daily_menu__center'
    ).all()
    
    if center_id:
        reservations = reservations.filter(daily_menu__center_id=center_id)
        guest_reservations = guest_reservations.filter(daily_menu__center_id=center_id)
    
    if start_date:
        reservations = reservations.filter(daily_menu__date__gte=start_date)
        guest_reservations = guest_reservations.filter(daily_menu__date__gte=start_date)
    
    if end_date:
        reservations = reservations.filter(daily_menu__date__lte=end_date)
        guest_reservations = guest_reservations.filter(daily_menu__date__lte=end_date)
    
    # گروه‌بندی بر اساس کاربر
    users_data = {}
    
    # رزروهای معمولی
    for reservation in reservations:
        user_id = reservation.user.id
        
        if user_id not in users_data:
            users_data[user_id] = {
                'user_id': user_id,
                'username': reservation.user.username,
                'full_name': reservation.user.get_full_name(),
                'employee_number': reservation.user.employee_number or '',
                'center_name': reservation.user.center.name if reservation.user.center else '',
                'total_reservations': 0,
                'total_guest_reservations': 0,
                'reserved_count': 0,
                'cancelled_count': 0,
                'served_count': 0,
                'total_amount': 0,
                'reserved_amount': 0,
            }
        
        data = users_data[user_id]
        data['total_reservations'] += 1
        
        if reservation.status == 'reserved':
            data['reserved_count'] += 1
            data['reserved_amount'] += float(reservation.amount or 0)
        elif reservation.status == 'cancelled':
            data['cancelled_count'] += 1
        elif reservation.status == 'served':
            data['served_count'] += 1
        
        data['total_amount'] += float(reservation.amount or 0)
    
    # رزروهای مهمان
    for guest_reservation in guest_reservations:
        user_id = guest_reservation.host_user.id
        
        if user_id not in users_data:
            users_data[user_id] = {
                'user_id': user_id,
                'username': guest_reservation.host_user.username,
                'full_name': guest_reservation.host_user.get_full_name(),
                'employee_number': guest_reservation.host_user.employee_number or '',
                'center_name': guest_reservation.host_user.center.name if guest_reservation.host_user.center else '',
                'total_reservations': 0,
                'total_guest_reservations': 0,
                'reserved_count': 0,
                'cancelled_count': 0,
                'served_count': 0,
                'total_amount': 0,
                'reserved_amount': 0,
            }
        
        data = users_data[user_id]
        data['total_guest_reservations'] += 1
        data['total_amount'] += float(guest_reservation.amount or 0)
        
        if guest_reservation.status == 'reserved':
            data['reserved_count'] += 1
            data['reserved_amount'] += float(guest_reservation.amount or 0)
        elif guest_reservation.status == 'cancelled':
            data['cancelled_count'] += 1
        elif guest_reservation.status == 'served':
            data['served_count'] += 1
    
    from decimal import Decimal
    for data in users_data.values():
        data['total_amount'] = Decimal(str(data['total_amount']))
        data['reserved_amount'] = Decimal(str(data['reserved_amount']))
    
    serializer = UserReportSerializer(list(users_data.values()), many=True)
    return Response(serializer.data)


@extend_schema(
    summary='Report by Date',
    description='Complete report of reservations by date',
    tags=['Reports'],
    parameters=[
        {
            'name': 'center_id',
            'in': 'query',
            'description': 'فیلتر بر اساس مرکز',
            'required': False,
            'schema': {'type': 'integer'}
        },
        {
            'name': 'start_date',
            'in': 'query',
            'description': 'تاریخ شروع (فرمت: YYYY-MM-DD یا YYYY/MM/DD)',
            'required': False,
            'schema': {'type': 'string'}
        },
        {
            'name': 'end_date',
            'in': 'query',
            'description': 'تاریخ پایان (فرمت: YYYY-MM-DD یا YYYY/MM/DD)',
            'required': False,
            'schema': {'type': 'string'}
        },
    ]
)
@api_view(['GET'])
@permission_classes([StatisticsPermission])
def report_by_date(request):
    """گزارش بر اساس تاریخ"""
    if not request.user.is_admin:
        return Response({
            'error': 'دسترسی غیرمجاز'
        }, status=status.HTTP_403_FORBIDDEN)
    
    center_id = request.query_params.get('center_id')
    start_date = parse_date_filter(request.query_params.get('start_date'))
    end_date = parse_date_filter(request.query_params.get('end_date'))
    
    # فیلتر رزروها
    reservations = FoodReservation.objects.select_related(
        'daily_menu__center'
    ).all()
    guest_reservations = GuestReservation.objects.select_related(
        'daily_menu__center'
    ).all()
    
    if center_id:
        reservations = reservations.filter(daily_menu__center_id=center_id)
        guest_reservations = guest_reservations.filter(daily_menu__center_id=center_id)
    
    if start_date:
        reservations = reservations.filter(daily_menu__date__gte=start_date)
        guest_reservations = guest_reservations.filter(daily_menu__date__gte=start_date)
    
    if end_date:
        reservations = reservations.filter(daily_menu__date__lte=end_date)
        guest_reservations = guest_reservations.filter(daily_menu__date__lte=end_date)
    
    # گروه‌بندی بر اساس تاریخ
    dates_data = {}
    
    for reservation in reservations:
        if not reservation.daily_menu:
            continue
        
        date = reservation.daily_menu.date
        
        if date not in dates_data:
            dates_data[date] = {
                'date': date,
                'jalali_date': jdatetime.date.fromgregorian(date=date).strftime('%Y/%m/%d'),
                'total_reservations': 0,
                'total_guest_reservations': 0,
                'reserved_count': 0,
                'cancelled_count': 0,
                'served_count': 0,
                'total_amount': 0,
                'reserved_amount': 0,
                'centers': {},
            }
        
        data = dates_data[date]
        data['total_reservations'] += 1
        
        center_name = reservation.daily_menu.center.name if reservation.daily_menu and reservation.daily_menu.center else 'نامشخص'
        if center_name not in data['centers']:
            data['centers'][center_name] = {
                'name': center_name,
                'total_reservations': 0,
                'total_amount': 0,
            }
        
        data['centers'][center_name]['total_reservations'] += 1
        data['centers'][center_name]['total_amount'] += float(reservation.amount or 0)
        
        if reservation.status == 'reserved':
            data['reserved_count'] += 1
            data['reserved_amount'] += float(reservation.amount or 0)
        elif reservation.status == 'cancelled':
            data['cancelled_count'] += 1
        elif reservation.status == 'served':
            data['served_count'] += 1
        
        data['total_amount'] += float(reservation.amount or 0)
    
    for guest_reservation in guest_reservations:
        if not guest_reservation.daily_menu:
            continue
        
        date = guest_reservation.daily_menu.date
        
        if date not in dates_data:
            dates_data[date] = {
                'date': date,
                'jalali_date': jdatetime.date.fromgregorian(date=date).strftime('%Y/%m/%d'),
                'total_reservations': 0,
                'total_guest_reservations': 0,
                'reserved_count': 0,
                'cancelled_count': 0,
                'served_count': 0,
                'total_amount': 0,
                'reserved_amount': 0,
                'centers': {},
            }
        
        data = dates_data[date]
        data['total_guest_reservations'] += 1
        
        center_name = guest_reservation.daily_menu.center.name if guest_reservation.daily_menu and guest_reservation.daily_menu.center else 'نامشخص'
        if center_name not in data['centers']:
            data['centers'][center_name] = {
                'name': center_name,
                'total_reservations': 0,
                'total_amount': 0,
            }
        
        data['total_amount'] += float(guest_reservation.amount or 0)
        
        if guest_reservation.status == 'reserved':
            data['reserved_count'] += 1
            data['reserved_amount'] += float(guest_reservation.amount or 0)
        elif guest_reservation.status == 'cancelled':
            data['cancelled_count'] += 1
        elif guest_reservation.status == 'served':
            data['served_count'] += 1
    
    from decimal import Decimal
    result = []
    for date in sorted(dates_data.keys(), reverse=True):
        data = dates_data[date]
        data['total_amount'] = Decimal(str(data['total_amount']))
        data['reserved_amount'] = Decimal(str(data['reserved_amount']))
        data['centers'] = list(data['centers'].values())
        for center_data in data['centers']:
            center_data['total_amount'] = Decimal(str(center_data['total_amount']))
        result.append(data)
    
    serializer = DateReportSerializer(result, many=True)
    return Response(serializer.data)


@extend_schema(
    summary='Comprehensive Report',
    description='Comprehensive report including all types of reports',
    tags=['Reports'],
    parameters=[
        {
            'name': 'center_id',
            'in': 'query',
            'description': 'فیلتر بر اساس مرکز',
            'required': False,
            'schema': {'type': 'integer'}
        },
        {
            'name': 'start_date',
            'in': 'query',
            'description': 'تاریخ شروع (فرمت: YYYY-MM-DD یا YYYY/MM/DD)',
            'required': False,
            'schema': {'type': 'string'}
        },
        {
            'name': 'end_date',
            'in': 'query',
            'description': 'تاریخ پایان (فرمت: YYYY-MM-DD یا YYYY/MM/DD)',
            'required': False,
            'schema': {'type': 'string'}
        },
    ]
)
@api_view(['GET'])
@permission_classes([StatisticsPermission])
def comprehensive_report(request):
    """گزارش جامع"""
    if not request.user.is_admin:
        return Response({
            'error': 'دسترسی غیرمجاز'
        }, status=status.HTTP_403_FORBIDDEN)
    
    center_id = request.query_params.get('center_id')
    start_date = parse_date_filter(request.query_params.get('start_date'))
    end_date = parse_date_filter(request.query_params.get('end_date'))
    
    # فیلتر رزروها
    reservations = FoodReservation.objects.select_related(
        'meal_option', 'meal_option__base_meal', 'meal_option__restaurant',
        'daily_menu__center', 'user'
    ).all()
    guest_reservations = GuestReservation.objects.select_related(
        'meal_option', 'meal_option__base_meal', 'meal_option__restaurant',
        'daily_menu__center', 'host_user'
    ).all()
    
    if center_id:
        reservations = reservations.filter(daily_menu__center_id=center_id)
        guest_reservations = guest_reservations.filter(daily_menu__center_id=center_id)
    
    if start_date:
        reservations = reservations.filter(daily_menu__date__gte=start_date)
        guest_reservations = guest_reservations.filter(daily_menu__date__gte=start_date)
    
    if end_date:
        reservations = reservations.filter(daily_menu__date__lte=end_date)
        guest_reservations = guest_reservations.filter(daily_menu__date__lte=end_date)
    
    from decimal import Decimal
    
    # آمار کلی
    total_reservations = reservations.count()
    total_guest_reservations = guest_reservations.count()
    total_amount = Decimal('0')
    reserved_amount = Decimal('0')
    served_amount = Decimal('0')
    cancelled_amount = Decimal('0')
    
    for reservation in reservations:
        amount = Decimal(str(reservation.amount or 0))
        total_amount += amount
        if reservation.status == 'reserved':
            reserved_amount += amount
        elif reservation.status == 'served':
            served_amount += amount
        elif reservation.status == 'cancelled':
            cancelled_amount += amount
    
    for guest_reservation in guest_reservations:
        amount = Decimal(str(guest_reservation.amount or 0))
        total_amount += amount
        if guest_reservation.status == 'reserved':
            reserved_amount += amount
        elif guest_reservation.status == 'served':
            served_amount += amount
        elif guest_reservation.status == 'cancelled':
            cancelled_amount += amount
    
    # گزارش بر اساس MealOption
    meal_options_data = {}
    for reservation in reservations:
        if not reservation.meal_option:
            continue
        
        meal_option = reservation.meal_option
        meal_option_id = meal_option.id
        
        if meal_option_id not in meal_options_data:
            meal_options_data[meal_option_id] = {
                'meal_option_id': meal_option_id,
                'meal_option_title': meal_option.title,
                'base_meal_title': meal_option.base_meal.title if meal_option.base_meal else '',
                'restaurant_name': meal_option.restaurant.name if meal_option.restaurant else '',
                'restaurant_id': meal_option.restaurant.id if meal_option.restaurant else None,
                'center_name': reservation.daily_menu.center.name if reservation.daily_menu and reservation.daily_menu.center else '',
                'center_id': reservation.daily_menu.center.id if reservation.daily_menu and reservation.daily_menu.center else None,
                'total_reservations': 0,
                'reserved_count': 0,
                'cancelled_count': 0,
                'served_count': 0,
                'total_amount': Decimal('0'),
                'reserved_amount': Decimal('0'),
                'served_amount': Decimal('0'),
            }
        
        data = meal_options_data[meal_option_id]
        data['total_reservations'] += 1
        amount = Decimal(str(reservation.amount or 0))
        data['total_amount'] += amount
        
        if reservation.status == 'reserved':
            data['reserved_count'] += 1
            data['reserved_amount'] += amount
        elif reservation.status == 'cancelled':
            data['cancelled_count'] += 1
        elif reservation.status == 'served':
            data['served_count'] += 1
            data['served_amount'] += amount
    
    # گزارش بر اساس BaseMeal
    base_meals_data = {}
    meal_options_by_base_meal = {}
    
    for reservation in reservations:
        if not reservation.meal_option or not reservation.meal_option.base_meal:
            continue
        
        base_meal = reservation.meal_option.base_meal
        base_meal_id = base_meal.id
        meal_option_id = reservation.meal_option.id
        
        if base_meal_id not in base_meals_data:
            base_meals_data[base_meal_id] = {
                'base_meal_id': base_meal_id,
                'base_meal_title': base_meal.title,
                'restaurant_name': reservation.meal_option.restaurant.name if reservation.meal_option.restaurant else '',
                'center_name': reservation.daily_menu.center.name if reservation.daily_menu and reservation.daily_menu.center else '',
                'meal_options_count': 0,
                'total_reservations': 0,
                'reserved_count': 0,
                'cancelled_count': 0,
                'served_count': 0,
                'total_amount': Decimal('0'),
            }
            meal_options_by_base_meal[base_meal_id] = {}
        
        data = base_meals_data[base_meal_id]
        data['total_reservations'] += 1
        amount = Decimal(str(reservation.amount or 0))
        data['total_amount'] += amount
        
        if reservation.status == 'reserved':
            data['reserved_count'] += 1
        elif reservation.status == 'cancelled':
            data['cancelled_count'] += 1
        elif reservation.status == 'served':
            data['served_count'] += 1
        
        if meal_option_id not in meal_options_by_base_meal[base_meal_id]:
            meal_options_by_base_meal[base_meal_id][meal_option_id] = {
                'meal_option_id': meal_option_id,
                'meal_option_title': reservation.meal_option.title,
                'base_meal_title': base_meal.title,
                'restaurant_name': reservation.meal_option.restaurant.name if reservation.meal_option.restaurant else '',
                'restaurant_id': reservation.meal_option.restaurant.id if reservation.meal_option.restaurant else None,
                'center_name': reservation.daily_menu.center.name if reservation.daily_menu and reservation.daily_menu.center else '',
                'center_id': reservation.daily_menu.center.id if reservation.daily_menu and reservation.daily_menu.center else None,
                'total_reservations': 0,
                'reserved_count': 0,
                'cancelled_count': 0,
                'served_count': 0,
                'total_amount': Decimal('0'),
                'reserved_amount': Decimal('0'),
                'served_amount': Decimal('0'),
            }
            data['meal_options_count'] += 1
        
        meal_option_data = meal_options_by_base_meal[base_meal_id][meal_option_id]
        meal_option_data['total_reservations'] += 1
        meal_option_data['total_amount'] += amount
        
        if reservation.status == 'reserved':
            meal_option_data['reserved_count'] += 1
            meal_option_data['reserved_amount'] += amount
        elif reservation.status == 'cancelled':
            meal_option_data['cancelled_count'] += 1
        elif reservation.status == 'served':
            meal_option_data['served_count'] += 1
            meal_option_data['served_amount'] += amount
    
    result_base_meals = []
    for base_meal_id, data in base_meals_data.items():
        data['meal_options'] = list(meal_options_by_base_meal[base_meal_id].values())
        result_base_meals.append(data)
    
    # گزارش بر اساس کاربر
    users_data = {}
    
    for reservation in reservations:
        user_id = reservation.user.id
        
        if user_id not in users_data:
            users_data[user_id] = {
                'user_id': user_id,
                'username': reservation.user.username,
                'full_name': reservation.user.get_full_name(),
                'employee_number': reservation.user.employee_number or '',
                'center_name': reservation.user.center.name if reservation.user.center else '',
                'total_reservations': 0,
                'total_guest_reservations': 0,
                'reserved_count': 0,
                'cancelled_count': 0,
                'served_count': 0,
                'total_amount': Decimal('0'),
                'reserved_amount': Decimal('0'),
            }
        
        data = users_data[user_id]
        data['total_reservations'] += 1
        amount = Decimal(str(reservation.amount or 0))
        data['total_amount'] += amount
        
        if reservation.status == 'reserved':
            data['reserved_count'] += 1
            data['reserved_amount'] += amount
        elif reservation.status == 'cancelled':
            data['cancelled_count'] += 1
        elif reservation.status == 'served':
            data['served_count'] += 1
    
    for guest_reservation in guest_reservations:
        user_id = guest_reservation.host_user.id
        
        if user_id not in users_data:
            users_data[user_id] = {
                'user_id': user_id,
                'username': guest_reservation.host_user.username,
                'full_name': guest_reservation.host_user.get_full_name(),
                'employee_number': guest_reservation.host_user.employee_number or '',
                'center_name': guest_reservation.host_user.center.name if guest_reservation.host_user.center else '',
                'total_reservations': 0,
                'total_guest_reservations': 0,
                'reserved_count': 0,
                'cancelled_count': 0,
                'served_count': 0,
                'total_amount': Decimal('0'),
                'reserved_amount': Decimal('0'),
            }
        
        data = users_data[user_id]
        data['total_guest_reservations'] += 1
        amount = Decimal(str(guest_reservation.amount or 0))
        data['total_amount'] += amount
        
        if guest_reservation.status == 'reserved':
            data['reserved_count'] += 1
            data['reserved_amount'] += amount
        elif guest_reservation.status == 'cancelled':
            data['cancelled_count'] += 1
        elif guest_reservation.status == 'served':
            data['served_count'] += 1
    
    # گزارش بر اساس تاریخ
    dates_data = {}
    
    for reservation in reservations:
        if not reservation.daily_menu:
            continue
        
        date = reservation.daily_menu.date
        
        if date not in dates_data:
            dates_data[date] = {
                'date': date,
                'jalali_date': jdatetime.date.fromgregorian(date=date).strftime('%Y/%m/%d'),
                'total_reservations': 0,
                'total_guest_reservations': 0,
                'reserved_count': 0,
                'cancelled_count': 0,
                'served_count': 0,
                'total_amount': Decimal('0'),
                'reserved_amount': Decimal('0'),
                'centers': {},
            }
        
        data = dates_data[date]
        data['total_reservations'] += 1
        amount = Decimal(str(reservation.amount or 0))
        data['total_amount'] += amount
        
        center_name = reservation.daily_menu.center.name if reservation.daily_menu and reservation.daily_menu.center else 'نامشخص'
        if center_name not in data['centers']:
            data['centers'][center_name] = {
                'name': center_name,
                'total_reservations': 0,
                'total_amount': Decimal('0'),
            }
        
        data['centers'][center_name]['total_reservations'] += 1
        data['centers'][center_name]['total_amount'] += amount
        
        if reservation.status == 'reserved':
            data['reserved_count'] += 1
            data['reserved_amount'] += amount
        elif reservation.status == 'cancelled':
            data['cancelled_count'] += 1
        elif reservation.status == 'served':
            data['served_count'] += 1
    
    for guest_reservation in guest_reservations:
        if not guest_reservation.daily_menu:
            continue
        
        date = guest_reservation.daily_menu.date
        
        if date not in dates_data:
            dates_data[date] = {
                'date': date,
                'jalali_date': jdatetime.date.fromgregorian(date=date).strftime('%Y/%m/%d'),
                'total_reservations': 0,
                'total_guest_reservations': 0,
                'reserved_count': 0,
                'cancelled_count': 0,
                'served_count': 0,
                'total_amount': Decimal('0'),
                'reserved_amount': Decimal('0'),
                'centers': {},
            }
        
        data = dates_data[date]
        data['total_guest_reservations'] += 1
        amount = Decimal(str(guest_reservation.amount or 0))
        data['total_amount'] += amount
        
        center_name = guest_reservation.daily_menu.center.name if guest_reservation.daily_menu and guest_reservation.daily_menu.center else 'نامشخص'
        if center_name not in data['centers']:
            data['centers'][center_name] = {
                'name': center_name,
                'total_reservations': 0,
                'total_amount': Decimal('0'),
            }
        
        if guest_reservation.status == 'reserved':
            data['reserved_count'] += 1
            data['reserved_amount'] += amount
        elif guest_reservation.status == 'cancelled':
            data['cancelled_count'] += 1
        elif guest_reservation.status == 'served':
            data['served_count'] += 1
    
    result_dates = []
    for date in sorted(dates_data.keys(), reverse=True):
        data = dates_data[date]
        data['centers'] = list(data['centers'].values())
        result_dates.append(data)
    
    # ساخت گزارش جامع
    report_data = {
        'total_reservations': total_reservations,
        'total_guest_reservations': total_guest_reservations,
        'total_amount': total_amount,
        'reserved_amount': reserved_amount,
        'served_amount': served_amount,
        'cancelled_amount': cancelled_amount,
        'by_meal_option': list(meal_options_data.values()),
        'by_base_meal': result_base_meals,
        'by_user': list(users_data.values()),
        'by_date': result_dates,
    }
    
    serializer = ComprehensiveReportSerializer(report_data)
    return Response(serializer.data)


@extend_schema(
    summary='Detailed Reservations Report',
    description='Complete detailed report of reservations with all information',
    tags=['Reports'],
    parameters=[
        {
            'name': 'center_id',
            'in': 'query',
            'description': 'فیلتر بر اساس مرکز',
            'required': False,
            'schema': {'type': 'integer'}
        },
        {
            'name': 'user_id',
            'in': 'query',
            'description': 'فیلتر بر اساس کاربر',
            'required': False,
            'schema': {'type': 'integer'}
        },
        {
            'name': 'start_date',
            'in': 'query',
            'description': 'تاریخ شروع (فرمت: YYYY-MM-DD یا YYYY/MM/DD)',
            'required': False,
            'schema': {'type': 'string'}
        },
        {
            'name': 'end_date',
            'in': 'query',
            'description': 'تاریخ پایان (فرمت: YYYY-MM-DD یا YYYY/MM/DD)',
            'required': False,
            'schema': {'type': 'string'}
        },
        {
            'name': 'status',
            'in': 'query',
            'description': 'فیلتر بر اساس وضعیت (reserved, cancelled, served)',
            'required': False,
            'schema': {'type': 'string'}
        },
    ]
)
@api_view(['GET'])
@permission_classes([StatisticsPermission])
def detailed_reservations_report(request):
    """گزارش جزئیات رزروها"""
    if not request.user.is_admin:
        return Response({
            'error': 'دسترسی غیرمجاز'
        }, status=status.HTTP_403_FORBIDDEN)
    
    center_id = request.query_params.get('center_id')
    user_id = request.query_params.get('user_id')
    start_date = parse_date_filter(request.query_params.get('start_date'))
    end_date = parse_date_filter(request.query_params.get('end_date'))
    status_filter = request.query_params.get('status')
    
    # فیلتر رزروها
    reservations = FoodReservation.objects.select_related(
        'user', 'meal_option', 'meal_option__base_meal', 'meal_option__restaurant',
        'daily_menu', 'daily_menu__center'
    ).all()
    
    if center_id:
        reservations = reservations.filter(daily_menu__center_id=center_id)
    
    if user_id:
        reservations = reservations.filter(user_id=user_id)
    
    if start_date:
        reservations = reservations.filter(daily_menu__date__gte=start_date)
    
    if end_date:
        reservations = reservations.filter(daily_menu__date__lte=end_date)
    
    if status_filter:
        reservations = reservations.filter(status=status_filter)
    
    serializer = DetailedReservationReportSerializer(reservations, many=True, context={'request': request})
    return Response(serializer.data)

