"""
Views for reservations app
"""
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, extend_schema_view
from drf_spectacular.types import OpenApiTypes
from django.utils import timezone
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
    GuestDessertReservationCreateSerializer, SimpleGuestDessertReservationSerializer
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
    description='Get summary of user reservations and guest reservations with full details',
    tags=['User Reservations']
)
@api_view(['GET'])
@permission_classes([FoodManagementPermission])
def user_reservations_summary(request):
    """خلاصه رزروهای کاربر با جزئیات کامل"""
    user = request.user
    
    # رزروهای شخصی
    personal_reservations = FoodReservation.objects.filter(user=user).select_related(
        'daily_menu', 'meal_option', 'meal_option__base_meal', 'meal_option__base_meal__restaurant'
    ).prefetch_related('meal_option__base_meal__restaurant__centers')
    personal_count = personal_reservations.count()
    personal_reserved = personal_reservations.filter(status='reserved').count()
    personal_cancelled = personal_reservations.filter(status='cancelled').count()
    personal_served = personal_reservations.filter(status='served').count()
    
    # جزئیات کامل رزروهای شخصی
    personal_reserved_items = personal_reservations.filter(status='reserved')
    personal_cancelled_items = personal_reservations.filter(status='cancelled')
    personal_served_items = personal_reservations.filter(status='served')
    personal_all_items = personal_reservations.all()
    
    # رزروهای مهمان
    guest_reservations = GuestReservation.objects.filter(host_user=user).select_related(
        'daily_menu', 'meal_option', 'meal_option__base_meal', 'meal_option__base_meal__restaurant'
    ).prefetch_related('meal_option__base_meal__restaurant__centers')
    guest_count = guest_reservations.count()
    guest_reserved = guest_reservations.filter(status='reserved').count()
    guest_cancelled = guest_reservations.filter(status='cancelled').count()
    guest_served = guest_reservations.filter(status='served').count()
    
    # جزئیات کامل رزروهای مهمان
    guest_reserved_items = guest_reservations.filter(status='reserved')
    guest_cancelled_items = guest_reservations.filter(status='cancelled')
    guest_served_items = guest_reservations.filter(status='served')
    guest_all_items = guest_reservations.all()
    
    # رزروهای امروز
    today = timezone.now().date()
    today_personal = personal_reservations.filter(daily_menu__date=today).count()
    today_guest = guest_reservations.filter(daily_menu__date=today).count()
    today_personal_items = personal_reservations.filter(daily_menu__date=today)
    today_guest_items = guest_reservations.filter(daily_menu__date=today)
    
    # استفاده از serializer برای جزئیات کامل
    personal_serializer = SimpleFoodReservationSerializer
    guest_serializer = SimpleGuestReservationSerializer
    
    return Response({
        'personal_reservations': {
            'total': personal_count,
            'reserved': personal_reserved,
            'cancelled': personal_cancelled,
            'served': personal_served,
            'today': today_personal,
            'items': {
                'all': personal_serializer(personal_all_items, many=True, context={'request': request}).data,
                'reserved': personal_serializer(personal_reserved_items, many=True, context={'request': request}).data,
                'cancelled': personal_serializer(personal_cancelled_items, many=True, context={'request': request}).data,
                'served': personal_serializer(personal_served_items, many=True, context={'request': request}).data,
                'today': personal_serializer(today_personal_items, many=True, context={'request': request}).data
            }
        },
        'guest_reservations': {
            'total': guest_count,
            'reserved': guest_reserved,
            'cancelled': guest_cancelled,
            'served': guest_served,
            'today': today_guest,
            'items': {
                'all': guest_serializer(guest_all_items, many=True, context={'request': request}).data,
                'reserved': guest_serializer(guest_reserved_items, many=True, context={'request': request}).data,
                'cancelled': guest_serializer(guest_cancelled_items, many=True, context={'request': request}).data,
                'served': guest_serializer(guest_served_items, many=True, context={'request': request}).data,
                'today': guest_serializer(today_guest_items, many=True, context={'request': request}).data
            }
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
    daily_menus = DailyMenu.objects.filter(
        restaurant__centers__in=user.centers.all(),
        date=parsed_date,
        is_available=True
    ).select_related('restaurant').prefetch_related(
        'restaurant__centers',
        'menu_meal_options', 
        'menu_meal_options__base_meal',
        'desserts'
    )
    
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
            if reservation.dessert:
                reservation.dessert.reserved_quantity = max(0, reservation.dessert.reserved_quantity - reservation.quantity)
                reservation.dessert.save()
            
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
            if reservation.dessert:
                reservation.dessert.reserved_quantity = max(0, reservation.dessert.reserved_quantity - 1)
                reservation.dessert.save()
            
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
        if reservation.dessert:
            reservation.dessert.reserved_quantity = max(0, reservation.dessert.reserved_quantity - reservation.quantity)
            reservation.dessert.save()
        
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
        if guest_reservation.dessert:
            guest_reservation.dessert.reserved_quantity = max(0, guest_reservation.dessert.reserved_quantity - 1)
            guest_reservation.dessert.save()
        
        response_serializer = SimpleGuestDessertReservationSerializer(guest_reservation)
        return Response(response_serializer.data)
    else:
        return Response(
            {'error': 'رزرو دسر مهمان قابل لغو نیست'}, 
            status=status.HTTP_400_BAD_REQUEST
        )

