"""
Views for reservations app
"""
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, extend_schema_view
from drf_spectacular.types import OpenApiTypes
from django.utils import timezone
from collections import defaultdict
from jalali_date import datetime2jalali, date2jalali
from apps.food_management.permissions import FoodManagementPermission
from apps.food_management.models import (
    FoodReservation, GuestReservation, DailyMenu,
    DessertReservation, GuestDessertReservation
)
from apps.food_management.utils import parse_date_filter
from apps.core.pagination import CustomPageNumberPagination
from apps.reservations.serializers import (
    FoodReservationSerializer, FoodReservationCreateSerializer,
    SimpleFoodReservationSerializer, GuestReservationSerializer,
    GuestReservationCreateSerializer, SimpleGuestReservationSerializer,
    DessertReservationSerializer, DessertReservationCreateSerializer,
    SimpleDessertReservationSerializer, GuestDessertReservationSerializer,
    GuestDessertReservationCreateSerializer, SimpleGuestDessertReservationSerializer,
    CombinedReservationCreateSerializer, CombinedReservationResponseSerializer
)
from apps.meals.serializers import SimpleEmployeeDailyMenuSerializer


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
        # System Admin می‌تواند همه رزروهای مهمان را ببیند
        if user.role == 'sys_admin':
            return GuestReservation.objects.all()
        # Food Admin و سایر کاربران فقط رزروهای مهمان خودشان را می‌بینند
        return GuestReservation.objects.filter(host_user=user)

    def perform_create(self, serializer):
        # همه کاربران (از جمله Food Admin) فقط می‌توانند رزرو مهمان برای خودشان ایجاد کنند
        serializer.save(host_user=self.request.user)


class GuestReservationDetailView(generics.RetrieveUpdateDestroyAPIView):
    """جزئیات رزرو مهمان"""
    serializer_class = SimpleGuestReservationSerializer
    permission_classes = [FoodManagementPermission]

    def get_queryset(self):
        user = self.request.user
        # System Admin می‌تواند همه رزروهای مهمان را ببیند
        if user.role == 'sys_admin':
            return GuestReservation.objects.all()
        # Food Admin و سایر کاربران فقط رزروهای مهمان خودشان را می‌بینند
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
    description='Get summary of user reservations and guest reservations with full details grouped by date and menu',
    tags=['User Reservations']
)
@api_view(['GET'])
@permission_classes([FoodManagementPermission])
def user_reservations_summary(request):
    """خلاصه رزروهای کاربر با جزئیات کامل - گروه‌بندی شده بر اساس تاریخ و منو"""
    user = request.user
    
    # رزروهای شخصی غذا
    personal_reservations = FoodReservation.objects.filter(user=user).select_related(
        'daily_menu', 'meal_option', 'meal_option__base_meal', 'meal_option__base_meal__restaurant',
        'daily_menu__restaurant'
    ).prefetch_related('meal_option__base_meal__restaurant__centers', 'daily_menu__restaurant__centers')
    
    # رزروهای شخصی دسر
    personal_dessert_reservations = DessertReservation.objects.filter(user=user).select_related(
        'daily_menu', 'dessert_option', 'dessert_option__base_dessert',
        'daily_menu__restaurant'
    ).prefetch_related('daily_menu__restaurant__centers')
    
    # رزروهای مهمان غذا
    guest_reservations = GuestReservation.objects.filter(host_user=user).select_related(
        'daily_menu', 'meal_option', 'meal_option__base_meal', 'meal_option__base_meal__restaurant',
        'daily_menu__restaurant'
    ).prefetch_related('meal_option__base_meal__restaurant__centers', 'daily_menu__restaurant__centers')
    
    # رزروهای مهمان دسر
    guest_dessert_reservations = GuestDessertReservation.objects.filter(host_user=user).select_related(
        'daily_menu', 'dessert_option', 'dessert_option__base_dessert',
        'daily_menu__restaurant'
    ).prefetch_related('daily_menu__restaurant__centers')
    
    # گروه‌بندی بر اساس تاریخ و منو
    def group_reservations_by_menu(reservations, dessert_reservations, request_obj=None, is_guest=False):
        """گروه‌بندی رزروها بر اساس تاریخ و منو"""
        grouped = defaultdict(lambda: {
            'date': None,
            'jalali_date': None,
            'daily_menu': None,
            'meals': [],
            'desserts': []
        })
        
        # تابع کمکی برای ساخت اطلاعات منو
        def create_menu_info(daily_menu):
            if not daily_menu:
                return None
            return {
                'id': daily_menu.id,
                'date': str(daily_menu.date),
                'jalali_date': date2jalali(daily_menu.date).strftime('%Y/%m/%d'),
                'restaurant': {
                    'id': daily_menu.restaurant.id if daily_menu.restaurant else None,
                    'name': daily_menu.restaurant.name if daily_menu.restaurant else None,
                } if daily_menu.restaurant else None
            }
        
        # گروه‌بندی رزروهای غذا
        for reservation in reservations:
            if not reservation.daily_menu:
                continue
                
            menu_key = reservation.daily_menu.id
            menu_date = reservation.daily_menu.date
            
            if menu_key not in grouped:
                grouped[menu_key] = {
                    'date': str(menu_date),
                    'jalali_date': date2jalali(menu_date).strftime('%Y/%m/%d'),
                    'daily_menu': create_menu_info(reservation.daily_menu),
                    'meals': [],
                    'desserts': []
                }
            
            # ساخت اطلاعات کامل غذا
            meal_option_data = None
            base_meal_data = None
            
            if reservation.meal_option:
                meal_option_data = {
                    'id': reservation.meal_option.id,
                    'title': reservation.meal_option.title,
                    'price': float(reservation.meal_option.price) if reservation.meal_option.price else None,
                    'description': reservation.meal_option.description or None
                }
                
                if reservation.meal_option.base_meal:
                    base_meal_data = {
                        'id': reservation.meal_option.base_meal.id,
                        'title': reservation.meal_option.base_meal.title,
                        'image': request_obj.build_absolute_uri(reservation.meal_option.base_meal.image.url) if request_obj and reservation.meal_option.base_meal.image else (reservation.meal_option.base_meal.image.url if reservation.meal_option.base_meal.image else None)
                    }
            elif reservation.meal_info:
                meal_option_data = {'title': reservation.meal_info}
            
            # افزودن غذا
            meal_data = {
                'id': reservation.id,
                'quantity': getattr(reservation, 'quantity', 1),
                'status': reservation.status,
                'amount': float(reservation.amount) if reservation.amount else 0.0,
                'reservation_date': reservation.reservation_date.isoformat() if reservation.reservation_date else None,
                'jalali_reservation_date': datetime2jalali(reservation.reservation_date).strftime('%Y/%m/%d %H:%M') if reservation.reservation_date else None,
                'meal_option': meal_option_data,
                'base_meal': base_meal_data
            }
            
            if is_guest:
                meal_data['guest_name'] = f"{reservation.guest_first_name} {reservation.guest_last_name}".strip()
            
            grouped[menu_key]['meals'].append(meal_data)
        
        # گروه‌بندی رزروهای دسر
        for reservation in dessert_reservations:
            if not reservation.daily_menu:
                continue
                
            menu_key = reservation.daily_menu.id
            
            if menu_key not in grouped:
                menu_date = reservation.daily_menu.date
                grouped[menu_key] = {
                    'date': str(menu_date),
                    'jalali_date': date2jalali(menu_date).strftime('%Y/%m/%d'),
                    'daily_menu': create_menu_info(reservation.daily_menu),
                    'meals': [],
                    'desserts': []
                }
            
            # ساخت اطلاعات کامل دسر
            dessert_option_data = None
            base_dessert_data = None
            
            if reservation.dessert_option:
                # اگر dessert_option موجود است، اطلاعات کامل را استخراج کن
                dessert_option_data = {
                    'id': reservation.dessert_option.id,
                    'title': reservation.dessert_option.title,
                    'price': float(reservation.dessert_option.price) if reservation.dessert_option.price else 0.0,
                    'description': reservation.dessert_option.description if reservation.dessert_option.description else None
                }
                
                if reservation.dessert_option.base_dessert:
                    base_dessert_data = {
                        'id': reservation.dessert_option.base_dessert.id,
                        'title': reservation.dessert_option.base_dessert.title,
                        'image': request_obj.build_absolute_uri(reservation.dessert_option.base_dessert.image.url) if request_obj and reservation.dessert_option.base_dessert.image else (reservation.dessert_option.base_dessert.image.url if reservation.dessert_option.base_dessert.image else None)
                    }
            elif reservation.dessert_option_info:
                # اگر فقط dessert_option_info موجود است (حذف شده)
                dessert_option_data = {
                    'id': None,
                    'title': reservation.dessert_option_info,
                    'price': None,
                    'description': None
                }
            
            # افزودن دسر
            dessert_data = {
                'id': reservation.id,
                'quantity': getattr(reservation, 'quantity', 1),
                'status': reservation.status,
                'amount': float(reservation.amount) if reservation.amount else 0.0,
                'reservation_date': reservation.reservation_date.isoformat() if reservation.reservation_date else None,
                'jalali_reservation_date': datetime2jalali(reservation.reservation_date).strftime('%Y/%m/%d %H:%M') if reservation.reservation_date else None,
                'dessert_option': dessert_option_data,
                'base_dessert': base_dessert_data
            }
            
            if is_guest:
                dessert_data['guest_name'] = f"{reservation.guest_first_name} {reservation.guest_last_name}".strip()
            
            grouped[menu_key]['desserts'].append(dessert_data)
        
        # تبدیل به لیست و مرتب‌سازی بر اساس تاریخ
        result = list(grouped.values())
        result.sort(key=lambda x: x['date'], reverse=True)
        
        return result
    
    # گروه‌بندی رزروهای شخصی
    personal_grouped = group_reservations_by_menu(personal_reservations, personal_dessert_reservations, request_obj=request, is_guest=False)
    
    # گروه‌بندی رزروهای مهمان
    guest_grouped = group_reservations_by_menu(guest_reservations, guest_dessert_reservations, request_obj=request, is_guest=True)
    
    # آمار کلی
    personal_count = personal_reservations.count()
    personal_dessert_count = personal_dessert_reservations.count()
    guest_count = guest_reservations.count()
    guest_dessert_count = guest_dessert_reservations.count()
    
    personal_reserved = personal_reservations.filter(status='reserved').count()
    personal_cancelled = personal_reservations.filter(status='cancelled').count()
    personal_served = personal_reservations.filter(status='served').count()
    
    guest_reserved = guest_reservations.filter(status='reserved').count()
    guest_cancelled = guest_reservations.filter(status='cancelled').count()
    guest_served = guest_reservations.filter(status='served').count()
    
    today = timezone.now().date()
    today_personal = personal_reservations.filter(daily_menu__date=today).count()
    today_guest = guest_reservations.filter(daily_menu__date=today).count()
    
    return Response({
        'personal_reservations': {
            'total': personal_count,
            'dessert_total': personal_dessert_count,
            'reserved': personal_reserved,
            'cancelled': personal_cancelled,
            'served': personal_served,
            'today': today_personal,
            'grouped_by_menu': personal_grouped
        },
        'guest_reservations': {
            'total': guest_count,
            'dessert_total': guest_dessert_count,
            'reserved': guest_reserved,
            'cancelled': guest_cancelled,
            'served': guest_served,
            'today': today_guest,
            'grouped_by_menu': guest_grouped
        },
        'total_today': today_personal + today_guest,
        'total_all': personal_count + guest_count
    })


# ========== Employee Menu and Reservation Management ==========

@extend_schema(
    operation_id='employee_daily_menus',
    summary='Get Daily Menus for Employee',
    description='Get simplified daily menus for employee\'s assigned centers on specific date (supports multiple centers). Returns only essential information: restaurant (id, name, center), date, and meals with their options (id, title, image, price, quantity, available_quantity).',
    tags=['Employee Management'],
    responses={
        200: SimpleEmployeeDailyMenuSerializer(many=True),
        400: {'description': 'Validation error'}
    }
)
@api_view(['GET'])
@permission_classes([FoodManagementPermission])
def employee_daily_menus(request):
    """منوهای روزانه برای کارمند - خروجی ساده"""
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
    # استفاده از distinct() برای جلوگیری از تکرار منوها وقتی یک رستوران به چندین مرکز متصل است
    daily_menus = DailyMenu.objects.filter(
        restaurant__centers__in=user.centers.all(),
        date=parsed_date,
        is_available=True
    ).select_related('restaurant').prefetch_related(
        'restaurant__centers',
        'menu_meal_options', 
        'menu_meal_options__base_meal',
        'menu_dessert_options',
        'menu_dessert_options__base_dessert'
    ).distinct().order_by('restaurant__name', 'date')
    
    serializer = SimpleEmployeeDailyMenuSerializer(daily_menus, many=True, context={'request': request})
    return Response(serializer.data)


@extend_schema(
    operation_id='employee_reservations',
    summary='Employee Reservations',
    description='Get all reservations for the authenticated employee or create a new reservation. Reservations use meal_option (DailyMenuMealOption) which is the actual meal with price and options.',
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
    if not user.centers.exists():
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
            # بررسی اینکه آیا رستوران به یکی از مراکز کاربر مرتبط است
            restaurant_centers = daily_menu.restaurant.centers.all() if daily_menu.restaurant else []
            if not any(user.has_center(center) for center in restaurant_centers):
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
    description='Create a guest reservation for the authenticated employee using meal_option (DailyMenuMealOption) which is the actual meal with price and options.',
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
        # بررسی اینکه آیا رستوران به یکی از مراکز کاربر مرتبط است
        restaurant_centers = daily_menu.restaurant.centers.all() if daily_menu.restaurant else []
        if not any(user.has_center(center) for center in restaurant_centers):
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
    description='Update a food reservation using meal_option (DailyMenuMealOption). (only own reservations)',
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
        # بررسی اینکه آیا رستوران به یکی از مراکز کاربر مرتبط است
        restaurant_centers = daily_menu.restaurant.centers.all() if daily_menu.restaurant else []
        if not any(user.has_center(center) for center in restaurant_centers):
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
    description='Update a guest reservation using meal_option (DailyMenuMealOption). (only own guest reservations)',
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
        # بررسی اینکه آیا رستوران به یکی از مراکز کاربر مرتبط است
        restaurant_centers = daily_menu.restaurant.centers.all() if daily_menu.restaurant else []
        if not any(user.has_center(center) for center in restaurant_centers):
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


# ========== Dessert Reservation Views ==========

@extend_schema_view(
    get=extend_schema(
        operation_id='dessert_reservation_list',
        summary='List Dessert Reservations',
        description='Get list of dessert reservations (admins: all, users: own reservations)',
        tags=['Dessert Reservations']
    ),
    post=extend_schema(
        operation_id='dessert_reservation_create',
        summary='Create Dessert Reservation',
        description='Create new dessert reservation for user',
        tags=['Dessert Reservations'],
        request=DessertReservationCreateSerializer,
        responses={
            201: SimpleDessertReservationSerializer,
            400: {'description': 'Validation error'},
            403: {'description': 'Permission denied'}
        }
    )
)
class DessertReservationListCreateView(generics.ListCreateAPIView):
    """لیست و ایجاد رزروهای دسر"""
    permission_classes = [FoodManagementPermission]
    pagination_class = CustomPageNumberPagination

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return DessertReservationCreateSerializer
        return DessertReservationSerializer

    def get_queryset(self):
        user = self.request.user
        if user.role in ['admin_food', 'sys_admin']:
            return DessertReservation.objects.all()
        return DessertReservation.objects.filter(user=user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class DessertReservationDetailView(generics.RetrieveUpdateDestroyAPIView):
    """جزئیات رزرو دسر"""
    serializer_class = SimpleDessertReservationSerializer
    permission_classes = [FoodManagementPermission]

    def get_queryset(self):
        user = self.request.user
        if user.role in ['admin_food', 'sys_admin']:
            return DessertReservation.objects.all()
        return DessertReservation.objects.filter(user=user)


@extend_schema(
    operation_id='user_dessert_reservation_limits',
    summary='Check User Dessert Reservation Limits',
    description='Check available and remaining dessert reservations for user on specific date',
    responses={
        200: OpenApiTypes.OBJECT,
        400: OpenApiTypes.OBJECT
    }
)
@api_view(['GET'])
@permission_classes([FoodManagementPermission])
def user_dessert_reservation_limits(request):
    """بررسی محدودیت‌های رزرو دسر کاربر - محدودیت رزرو برداشته شده است"""
    user = request.user
    date = request.query_params.get('date')
    
    if not date:
        return Response({
            'error': 'تاریخ الزامی است'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    parsed_date = parse_date_filter(date)
    if not parsed_date:
        return Response({
            'error': 'فرمت تاریخ نامعتبر است. از فرمت میلادی (2025-10-24) یا شمسی (1404/08/02) استفاده کنید'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    current_reservations = DessertReservation.get_user_date_reservations_count(user, parsed_date)
    
    return Response({
        'user': {
            'id': user.id,
            'username': user.username,
            'full_name': f"{user.first_name} {user.last_name}".strip(),
        },
        'date': date,
        'current_reservations': current_reservations,
        'unlimited': True,
        'can_reserve': True
    })


@api_view(['POST'])
@permission_classes([FoodManagementPermission])
def cancel_dessert_reservation(request, reservation_id):
    """لغو رزرو دسر"""
    try:
        reservation = DessertReservation.objects.get(
            id=reservation_id,
            user=request.user
        )
        
        if reservation.cancel():
            # به‌روزرسانی reserved_quantity
            if reservation.dessert_option:
                reservation.dessert_option.reserved_quantity = max(0, reservation.dessert_option.reserved_quantity - reservation.quantity)
                reservation.dessert_option.save()
            
            return Response({
                'message': 'رزرو دسر با موفقیت لغو شد.'
            })
        else:
            return Response({
                'error': 'امکان لغو این رزرو وجود ندارد.'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    except DessertReservation.DoesNotExist:
        return Response({
            'error': 'رزرو مورد نظر یافت نشد.'
        }, status=status.HTTP_404_NOT_FOUND)


# ========== Combined Reservation View ==========

@extend_schema(
    operation_id='combined_reservation_create',
    summary='Create Combined Food and Dessert Reservation',
    description='Create food and/or dessert reservation in a single request. At least one of meal_option or dessert_option must be provided.',
    tags=['Reservations'],
    request=CombinedReservationCreateSerializer,
    responses={
        201: {
            'description': 'Reservations created successfully',
            'content': {
                'application/json': {
                    'schema': {
                        'type': 'object',
                        'properties': {
                            'meal_reservation': {'type': 'object', 'nullable': True},
                            'dessert_reservation': {'type': 'object', 'nullable': True}
                        }
                    }
                }
            }
        },
        400: {'description': 'Validation error'},
        403: {'description': 'Permission denied'}
    }
)
@api_view(['POST'])
@permission_classes([FoodManagementPermission])
def combined_reservation_create(request):
    """ایجاد رزرو یکپارچه غذا و دسر"""
    serializer = CombinedReservationCreateSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        # بررسی اینکه daily_menu متعلق به یکی از مراکز کاربر است
        daily_menu = serializer.validated_data['daily_menu']
        restaurant_centers = daily_menu.restaurant.centers.all() if daily_menu.restaurant else []
        
        if not any(request.user.has_center(center) for center in restaurant_centers):
            return Response(
                {'error': 'شما نمی‌توانید برای این مرکز رزرو کنید'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # ایجاد رزروها
        results = serializer.save()
        
        # ساخت response با serializer ساده
        response_serializer = CombinedReservationResponseSerializer(results)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ========== Guest Dessert Reservation Views ==========

@extend_schema_view(
    get=extend_schema(
        operation_id='guest_dessert_reservation_list',
        summary='List Guest Dessert Reservations',
        description='Get list of guest dessert reservations (admins: all, users: own guest reservations)',
        tags=['Guest Dessert Reservations']
    ),
    post=extend_schema(
        operation_id='guest_dessert_reservation_create',
        summary='Create Guest Dessert Reservation',
        description='Create dessert reservation for guest',
        tags=['Guest Dessert Reservations']
    )
)
class GuestDessertReservationListCreateView(generics.ListCreateAPIView):
    """لیست و ایجاد رزروهای دسر مهمان"""
    permission_classes = [FoodManagementPermission]
    pagination_class = CustomPageNumberPagination

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return GuestDessertReservationCreateSerializer
        return GuestDessertReservationSerializer

    def get_queryset(self):
        user = self.request.user
        if user.role in ['admin_food', 'sys_admin']:
            return GuestDessertReservation.objects.all()
        return GuestDessertReservation.objects.filter(host_user=user)

    def perform_create(self, serializer):
        serializer.save(host_user=self.request.user)


class GuestDessertReservationDetailView(generics.RetrieveUpdateDestroyAPIView):
    """جزئیات رزرو دسر مهمان"""
    serializer_class = SimpleGuestDessertReservationSerializer
    permission_classes = [FoodManagementPermission]

    def get_queryset(self):
        user = self.request.user
        if user.role in ['admin_food', 'sys_admin']:
            return GuestDessertReservation.objects.all()
        return GuestDessertReservation.objects.filter(host_user=user)


@extend_schema(
    operation_id='user_guest_dessert_reservation_limits',
    summary='Check User Guest Dessert Reservation Limits',
    description='Check available and remaining guest dessert reservations for user on specific date',
    responses={
        200: OpenApiTypes.OBJECT,
        400: OpenApiTypes.OBJECT
    }
)
@api_view(['GET'])
@permission_classes([FoodManagementPermission])
def user_guest_dessert_reservation_limits(request):
    """بررسی محدودیت‌های رزرو دسر مهمان کاربر - محدودیت رزرو برداشته شده است"""
    user = request.user
    date = request.query_params.get('date')
    
    if not date:
        return Response({
            'error': 'تاریخ الزامی است'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    parsed_date = parse_date_filter(date)
    if not parsed_date:
        return Response({
            'error': 'فرمت تاریخ نامعتبر است. از فرمت میلادی (2025-10-24) یا شمسی (1404/08/02) استفاده کنید'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    current_guest_reservations = GuestDessertReservation.get_user_date_guest_reservations_count(user, parsed_date)
    
    return Response({
        'user': {
            'id': user.id,
            'username': user.username,
            'full_name': f"{user.first_name} {user.last_name}".strip(),
        },
        'date': date,
        'current_guest_reservations': current_guest_reservations,
        'unlimited': True,
        'can_reserve_guest': True
    })


@extend_schema(
    operation_id='cancel_guest_dessert_reservation',
    summary='Cancel Guest Dessert Reservation',
    description='Cancel guest dessert reservation by host user',
    responses={
        200: OpenApiTypes.OBJECT,
        400: OpenApiTypes.OBJECT,
        404: OpenApiTypes.OBJECT
    }
)
@api_view(['POST'])
@permission_classes([FoodManagementPermission])
def cancel_guest_dessert_reservation(request, reservation_id):
    """لغو رزرو دسر مهمان"""
    try:
        reservation = GuestDessertReservation.objects.get(
            id=reservation_id,
            host_user=request.user
        )
        
        if reservation.cancel():
            # به‌روزرسانی reserved_quantity
            if reservation.dessert_option:
                reservation.dessert_option.reserved_quantity = max(0, reservation.dessert_option.reserved_quantity - 1)
                reservation.dessert_option.save()
            
            return Response({
                'message': 'رزرو دسر مهمان با موفقیت لغو شد.'
            })
        else:
            return Response({
                'error': 'امکان لغو این رزرو دسر مهمان وجود ندارد.'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    except GuestDessertReservation.DoesNotExist:
        return Response({
            'error': 'رزرو دسر مهمان مورد نظر یافت نشد.'
        }, status=status.HTTP_404_NOT_FOUND)


@extend_schema(
    operation_id='user_dessert_reservations',
    summary='Get User Dessert Reservations',
    description='Get all dessert reservations for the authenticated user',
    tags=['User Reservations']
)
@api_view(['GET'])
@permission_classes([FoodManagementPermission])
def user_dessert_reservations(request):
    """رزروهای دسر کاربر"""
    user = request.user
    reservations = DessertReservation.objects.filter(user=user).order_by('-reservation_date')
    
    date = request.query_params.get('date')
    if date:
        parsed_date = parse_date_filter(date)
        if parsed_date:
            reservations = reservations.filter(daily_menu__date=parsed_date)
    
    status_filter = request.query_params.get('status')
    if status_filter:
        reservations = reservations.filter(status=status_filter)
    
    serializer = SimpleDessertReservationSerializer(reservations, many=True)
    return Response(serializer.data)


@extend_schema(
    operation_id='user_guest_dessert_reservations',
    summary='Get User Guest Dessert Reservations',
    description='Get all guest dessert reservations made by the authenticated user',
    tags=['User Reservations']
)
@api_view(['GET'])
@permission_classes([FoodManagementPermission])
def user_guest_dessert_reservations(request):
    """رزروهای دسر مهمان کاربر"""
    user = request.user
    guest_reservations = GuestDessertReservation.objects.filter(host_user=user).order_by('-reservation_date')
    
    date = request.query_params.get('date')
    if date:
        parsed_date = parse_date_filter(date)
        if parsed_date:
            guest_reservations = guest_reservations.filter(daily_menu__date=parsed_date)
    
    status_filter = request.query_params.get('status')
    if status_filter:
        guest_reservations = guest_reservations.filter(status=status_filter)
    
    serializer = SimpleGuestDessertReservationSerializer(guest_reservations, many=True)
    return Response(serializer.data)


# ========== Employee Dessert Reservation Views ==========

@extend_schema(
    operation_id='employee_dessert_reservations',
    summary='Get/Create Dessert Reservations (Employee)',
    description='GET: Get all dessert reservations for the authenticated employee. POST: Create a new dessert reservation for the authenticated employee.',
    tags=['Employee Management'],
    request=DessertReservationCreateSerializer,
    responses={
        200: SimpleDessertReservationSerializer(many=True),
        201: SimpleDessertReservationSerializer,
        400: {'description': 'Validation error'},
        403: {'description': 'Permission denied'}
    }
)
@api_view(['GET', 'POST'])
@permission_classes([FoodManagementPermission])
def employee_dessert_reservations(request):
    """رزروهای دسر کارمند"""
    user = request.user
    
    if not user.centers.exists():
        return Response(
            {'error': 'کاربر مرکز مشخصی ندارد'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if request.method == 'GET':
        reservations = DessertReservation.objects.filter(user=user).order_by('-reservation_date')
        
        date = request.query_params.get('date')
        if date:
            parsed_date = parse_date_filter(date)
            if parsed_date:
                reservations = reservations.filter(daily_menu__date=parsed_date)
        
        status_filter = request.query_params.get('status')
        if status_filter:
            reservations = reservations.filter(status=status_filter)
        
        serializer = SimpleDessertReservationSerializer(reservations, many=True)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        serializer = DessertReservationCreateSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            daily_menu = serializer.validated_data['daily_menu']
            restaurant_centers = daily_menu.restaurant.centers.all() if daily_menu.restaurant else []
            if not any(user.has_center(center) for center in restaurant_centers):
                return Response(
                    {'error': 'شما نمی‌توانید برای این مرکز رزرو کنید'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            reservation = serializer.save(user=user)
            response_serializer = SimpleDessertReservationSerializer(reservation)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    operation_id='employee_create_guest_dessert_reservation',
    summary='Create Guest Dessert Reservation (Employee)',
    description='Create a guest dessert reservation for the authenticated employee.',
    tags=['Employee Management']
)
@api_view(['POST'])
@permission_classes([FoodManagementPermission])
def employee_create_guest_dessert_reservation(request):
    """ایجاد رزرو دسر مهمان برای کارمند"""
    user = request.user
    
    if not user.centers.exists():
        return Response(
            {'error': 'کاربر مرکز مشخصی ندارد'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    serializer = GuestDessertReservationCreateSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        daily_menu = serializer.validated_data['daily_menu']
        restaurant_centers = daily_menu.restaurant.centers.all() if daily_menu.restaurant else []
        if not any(user.has_center(center) for center in restaurant_centers):
            return Response(
                {'error': 'شما نمی‌توانید برای این مرکز رزرو کنید'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        guest_reservation = serializer.save(host_user=user)
        response_serializer = SimpleGuestDessertReservationSerializer(guest_reservation)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    operation_id='employee_update_dessert_reservation',
    summary='Update Dessert Reservation (Employee)',
    description='Update a dessert reservation (only own reservations)',
    tags=['Employee Management'],
    request=DessertReservationCreateSerializer,
    responses={
        200: SimpleDessertReservationSerializer,
        400: {'description': 'Validation error'},
        403: {'description': 'Permission denied'},
        404: {'description': 'Reservation not found'}
    }
)
@api_view(['PUT', 'PATCH'])
@permission_classes([FoodManagementPermission])
def employee_update_dessert_reservation(request, reservation_id):
    """ویرایش رزرو دسر برای کارمند"""
    user = request.user
    
    try:
        reservation = DessertReservation.objects.get(id=reservation_id, user=user)
    except DessertReservation.DoesNotExist:
        return Response(
            {'error': 'رزرو یافت نشد'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    
    if reservation.status != 'reserved':
        return Response(
            {'error': 'فقط رزروهای فعال قابل ویرایش هستند'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    serializer = DessertReservationCreateSerializer(
        reservation, 
        data=request.data, 
        partial=request.method == 'PATCH',
        context={'request': request}
    )
    
    if serializer.is_valid():
        daily_menu = serializer.validated_data['daily_menu']
        restaurant_centers = daily_menu.restaurant.centers.all() if daily_menu.restaurant else []
        if not any(user.has_center(center) for center in restaurant_centers):
            return Response(
                {'error': 'شما نمی‌توانید برای این مرکز رزرو کنید'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer.save()
        response_serializer = SimpleDessertReservationSerializer(reservation)
        return Response(response_serializer.data)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    operation_id='employee_update_guest_dessert_reservation',
    summary='Update Guest Dessert Reservation (Employee)',
    description='Update a guest dessert reservation (only own guest reservations)',
    tags=['Employee Management'],
    request=GuestDessertReservationCreateSerializer,
    responses={
        200: SimpleGuestDessertReservationSerializer,
        400: {'description': 'Validation error'},
        403: {'description': 'Permission denied'},
        404: {'description': 'Guest reservation not found'}
    }
)
@api_view(['PUT', 'PATCH'])
@permission_classes([FoodManagementPermission])
def employee_update_guest_dessert_reservation(request, guest_reservation_id):
    """ویرایش رزرو دسر مهمان برای کارمند"""
    user = request.user
    
    try:
        guest_reservation = GuestDessertReservation.objects.get(id=guest_reservation_id, host_user=user)
    except GuestDessertReservation.DoesNotExist:
        return Response(
            {'error': 'رزرو دسر مهمان یافت نشد'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    
    if guest_reservation.status != 'reserved':
        return Response(
            {'error': 'فقط رزروهای فعال قابل ویرایش هستند'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    serializer = GuestDessertReservationCreateSerializer(
        guest_reservation, 
        data=request.data, 
        partial=request.method == 'PATCH',
        context={'request': request}
    )
    
    if serializer.is_valid():
        daily_menu = serializer.validated_data['daily_menu']
        restaurant_centers = daily_menu.restaurant.centers.all() if daily_menu.restaurant else []
        if not any(user.has_center(center) for center in restaurant_centers):
            return Response(
                {'error': 'شما نمی‌توانید برای این مرکز رزرو کنید'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer.save()
        response_serializer = SimpleGuestDessertReservationSerializer(guest_reservation)
        return Response(response_serializer.data)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    operation_id='employee_cancel_dessert_reservation',
    summary='Cancel Dessert Reservation (Employee)',
    description='Cancel a dessert reservation (only own reservations)',
    tags=['Employee Management']
)
@api_view(['POST'])
@permission_classes([FoodManagementPermission])
def employee_cancel_dessert_reservation(request, reservation_id):
    """لغو رزرو دسر برای کارمند"""
    user = request.user
    
    try:
        reservation = DessertReservation.objects.get(id=reservation_id, user=user)
    except DessertReservation.DoesNotExist:
        return Response(
            {'error': 'رزرو یافت نشد'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    
    if reservation.cancel():
        if reservation.dessert_option:
            reservation.dessert_option.reserved_quantity = max(0, reservation.dessert_option.reserved_quantity - reservation.quantity)
            reservation.dessert_option.save()
        
        response_serializer = SimpleDessertReservationSerializer(reservation)
        return Response(response_serializer.data)
    else:
        return Response(
            {'error': 'رزرو قابل لغو نیست'}, 
            status=status.HTTP_400_BAD_REQUEST
        )


@extend_schema(
    operation_id='employee_cancel_guest_dessert_reservation',
    summary='Cancel Guest Dessert Reservation (Employee)',
    description='Cancel a guest dessert reservation (only own guest reservations)',
    tags=['Employee Management']
)
@api_view(['POST'])
@permission_classes([FoodManagementPermission])
def employee_cancel_guest_dessert_reservation(request, guest_reservation_id):
    """لغو رزرو دسر مهمان برای کارمند"""
    user = request.user
    
    try:
        guest_reservation = GuestDessertReservation.objects.get(id=guest_reservation_id, host_user=user)
    except GuestDessertReservation.DoesNotExist:
        return Response(
            {'error': 'رزرو دسر مهمان یافت نشد'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    
    if guest_reservation.cancel():
        if guest_reservation.dessert_option:
            guest_reservation.dessert_option.reserved_quantity = max(0, guest_reservation.dessert_option.reserved_quantity - 1)
            guest_reservation.dessert_option.save()
        
        response_serializer = SimpleGuestDessertReservationSerializer(guest_reservation)
        return Response(response_serializer.data)
    else:
        return Response(
            {'error': 'رزرو دسر مهمان قابل لغو نیست'}, 
            status=status.HTTP_400_BAD_REQUEST
        )

