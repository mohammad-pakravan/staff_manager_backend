"""
Views for meals app
"""
from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, extend_schema_view , OpenApiParameter, OpenApiResponse
from drf_spectacular.types import OpenApiTypes
from django.utils import timezone
from datetime import timedelta
from apps.food_management.permissions import (
    IsFoodAdminOrSystemAdmin,
    FoodManagementPermission
)
from apps.food_management.models import (
    DailyMenuDessertOption, DessertReservation, FoodReservation, Restaurant, BaseMeal, DailyMenu, DailyMenuMealOption,
    Dessert
)
from apps.food_management.utils import parse_date_filter
from apps.core.pagination import CustomPageNumberPagination
 
from apps.reservations.serializers import FoodReservationSerializer, SimpleFoodReservationSerializer

# برای سازگاری با کدهای قبلی
Meal = BaseMeal
from apps.meals.serializers import (
    RestaurantSerializer, MealSerializer, SimpleBaseMealSerializer,
    SimpleRestaurantSerializer, DailyMenuSerializer,
    DailyMenuMealUpdateSerializer,
    DessertSerializer, SimpleDessertSerializer
)


from apps.accounts.models import User

# ========== Meal Management ==========

@extend_schema_view(
    get=extend_schema(
        operation_id='meal_list',
        summary='List Meals',
        description='Get list of all base meals (food groups). Meal options (DailyMenuMealOption) are managed per DailyMenu via admin panel.',
        tags=['Meals']
    ),
    post=extend_schema(
        operation_id='meal_create',
        summary='Create Meal',
        description='Create new base meal (food group). After creation, add meal options (DailyMenuMealOption) via admin panel when creating/editing a DailyMenu. (only for food admins and system admins). Returns simplified meal data without restaurant details.',
        tags=['Meals'],
        request=MealSerializer,
        responses={
            201: SimpleBaseMealSerializer,
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
        # ادمین سیستم همه غذاها را می‌بیند
        # ادمین غذا فقط غذاهای رستوران‌های مراکز خود را می‌بیند
        # کاربران عادی فقط غذاهای مرکز خود را می‌بینند
        user = self.request.user
        if user.role == 'sys_admin':
            return Meal.objects.all()
        elif user.role == 'admin_food':
            # ادمین غذا: فقط غذاهای رستوران‌هایی که به مراکز ادمین غذا متصل هستند
            if user.centers.exists():
                return Meal.objects.filter(
                    restaurant__centers__in=user.centers.all()
                ).distinct()
            return Meal.objects.none()
        elif user.centers.exists():
            return Meal.objects.filter(is_active=True, restaurant__centers__in=user.centers.all()).distinct()
        return Meal.objects.none()
    
    def create(self, request, *args, **kwargs):
        # فقط ادمین غذا می‌تواند غذا ایجاد کند
        user = request.user
        if user.role != 'admin_food':
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("فقط ادمین غذا می‌تواند غذا ایجاد کند")
        
        # استفاده از serializer کامل برای ایجاد
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        meal = serializer.save()
        
        # برگرداندن response با serializer ساده
        response_serializer = SimpleBaseMealSerializer(meal, context={'request': request})
        headers = self.get_success_headers(response_serializer.data)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED, headers=headers)


@extend_schema_view(
    get=extend_schema(
        operation_id='meal_detail',
        summary='Get Meal Details',
        description='Get base meal details. Returns simplified meal data without restaurant information.',
        tags=['Meals'],
        responses={
            200: SimpleBaseMealSerializer,
            404: {'description': 'Meal not found'}
        }
    ),
    put=extend_schema(
        operation_id='meal_update',
        summary='Update Meal',
        description='Update base meal. Note: Meal options (DailyMenuMealOption) should be managed via admin panel when creating/editing a DailyMenu. (only for admins). Returns simplified meal data without restaurant information.',
        tags=['Meals'],
        request=MealSerializer,
        responses={
            200: SimpleBaseMealSerializer,
            400: {'description': 'Validation error'},
            403: {'description': 'Permission denied'},
            404: {'description': 'Meal not found'}
        }
    ),
    patch=extend_schema(
        operation_id='meal_partial_update',
        summary='Partial Update Meal',
        description='Partially update base meal. Note: Meal options (DailyMenuMealOption) should be managed via admin panel when creating/editing a DailyMenu. (only for admins). Returns simplified meal data without restaurant information.',
        tags=['Meals'],
        request=MealSerializer,
        responses={
            200: SimpleBaseMealSerializer,
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
        if user.role == 'sys_admin':
            return Meal.objects.all()
        elif user.role == 'admin_food':
            # ادمین غذا: فقط غذاهای رستوران‌هایی که به مراکز ادمین غذا متصل هستند
            if user.centers.exists():
                return Meal.objects.filter(
                    restaurant__centers__in=user.centers.all()
                ).distinct()
            return Meal.objects.none()
        # کاربران عادی فقط غذاهای مرکز خود را می‌بینند
        elif user.centers.exists():
            return Meal.objects.filter(restaurant__centers__in=user.centers.all()).distinct()
        else:
            return Meal.objects.none()
    
    def retrieve(self, request, *args, **kwargs):
        """بازگرداندن جزئیات غذا با serializer ساده"""
        instance = self.get_object()
        serializer = SimpleBaseMealSerializer(instance, context={'request': request})
        return Response(serializer.data)
    
    def update(self, request, *args, **kwargs):
        """به‌روزرسانی کامل غذا - فقط ادمین غذا"""
        user = request.user
        if user.role != 'admin_food':
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("فقط ادمین غذا می‌تواند غذا را ویرایش کند")
        
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        # استفاده از serializer کامل برای validation و update
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        meal = serializer.save()
        
        # برگرداندن response با serializer ساده
        response_serializer = SimpleBaseMealSerializer(meal, context={'request': request})
        return Response(response_serializer.data)
    
    def partial_update(self, request, *args, **kwargs):
        """به‌روزرسانی جزئی غذا"""
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        """حذف غذا - فقط ادمین غذا"""
        user = request.user
        if user.role != 'admin_food':
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("فقط ادمین غذا می‌تواند غذا را حذف کند")
        return super().destroy(request, *args, **kwargs)


# ========== Restaurant Meals ==========

@extend_schema(
    operation_id='restaurant_meals',
    summary='Get Meals by Restaurant',
    description='Get list of meals for a specific restaurant. Food admin can only see meals of restaurants that belong to their assigned centers. Returns only meal data without restaurant information. No pagination.',
    tags=['Meals'],
    parameters=[
        {
            'name': 'restaurant_id',
            'in': 'path',
            'description': 'ID of the restaurant',
            'required': True,
            'schema': {'type': 'integer'}
        }
    ],
    responses={
        200: SimpleBaseMealSerializer(many=True),
        403: {'description': 'Permission denied'},
        404: {'description': 'Restaurant not found'}
    }
)
@api_view(['GET'])
@permission_classes([FoodManagementPermission])
def restaurant_meals(request, restaurant_id):
    """لیست غذاهای یک رستوران خاص - فقط رستوران‌هایی که کاربر به آن‌ها دسترسی دارد"""
    user = request.user
    
    # ساخت queryset بر اساس دسترسی کاربر
    if user.role == 'sys_admin':
        # System Admin به همه رستوران‌ها دسترسی دارد
        restaurants_qs = Restaurant.objects.all()
    elif user.role == 'admin_food':
        # ادمین غذا: فقط رستوران‌هایی که به مراکز ادمین غذا متصل هستند
        if not user.centers.exists():
            return Response({
                'error': 'کاربر مرکز مشخصی ندارد'
            }, status=status.HTTP_400_BAD_REQUEST)
        restaurants_qs = Restaurant.objects.filter(centers__in=user.centers.all()).distinct()
    else:
        # کاربران عادی: فقط رستوران‌های مراکز خود
        if not user.centers.exists():
            return Response({
                'error': 'کاربر مرکز مشخصی ندارد'
            }, status=status.HTTP_400_BAD_REQUEST)
        restaurants_qs = Restaurant.objects.filter(centers__in=user.centers.all(), is_active=True).distinct()
    
    # بررسی اینکه رستوران در لیست رستوران‌های قابل دسترسی کاربر است
    try:
        restaurant = restaurants_qs.get(id=restaurant_id)
    except Restaurant.DoesNotExist:
        return Response({
            'error': 'رستوران یافت نشد یا شما به این رستوران دسترسی ندارید'
        }, status=status.HTTP_404_NOT_FOUND)
    
    # دریافت غذاهای رستوران
    meals = Meal.objects.filter(restaurant=restaurant)
    
    # برای کاربران عادی فقط غذاهای فعال
    if user.role not in ['sys_admin', 'admin_food']:
        meals = meals.filter(is_active=True)
    
    # استفاده از serializer ساده (بدون اطلاعات رستوران)
    serializer = SimpleBaseMealSerializer(meals, many=True, context={'request': request})
    return Response(serializer.data)


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
        # System Admin sees all restaurants
        if user.role == 'sys_admin':
            return Restaurant.objects.all()
        # Food Admin sees only restaurants of their assigned centers
        if user.role == 'admin_food':
            if user.centers.exists():
                return Restaurant.objects.filter(centers__in=user.centers.all()).distinct()
            return Restaurant.objects.none()
        # Employees see only their centers' active restaurants
        if user.centers.exists():
            return Restaurant.objects.filter(centers__in=user.centers.all(), is_active=True).distinct()
        return Restaurant.objects.none()

    def perform_create(self, serializer):
        user = self.request.user
        # Food Admin می‌تواند رستوران برای مراکز خودش و مراکز دیگر ایجاد کند
        # System Admin می‌تواند رستوران برای هر مرکزی ایجاد کند
        # هیچ محدودیتی اعمال نمی‌کنیم - ادمین غذا می‌تواند هر مرکزی را انتخاب کند
        serializer.save()


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
        # System Admin sees all restaurants
        if user.role == 'sys_admin':
            return Restaurant.objects.all()
        # Food Admin sees only restaurants of their assigned centers
        if user.role == 'admin_food':
            if user.centers.exists():
                return Restaurant.objects.filter(centers__in=user.centers.all()).distinct()
            return Restaurant.objects.none()
        # Employees see only their centers' active restaurants
        if user.centers.exists():
            return Restaurant.objects.filter(centers__in=user.centers.all(), is_active=True).distinct()
        return Restaurant.objects.none()
    
    def update(self, request, *args, **kwargs):
        """به‌روزرسانی رستوران - Food Admin می‌تواند رستوران‌های مراکز خودش را ویرایش کند و مراکز را به مراکز خودش و مراکز دیگر تغییر دهد"""
        user = request.user
        if user.role == 'admin_food':
            # برای Food Admin، باید بررسی کنیم که آیا رستوران به یکی از مراکز او تعلق دارد یا نه
            # اگر تعلق دارد، می‌تواند آن را ویرایش کند و مراکز را به مراکز خودش اضافه کند
            instance_id = kwargs.get('pk')
            try:
                instance = Restaurant.objects.get(id=instance_id)
            except Restaurant.DoesNotExist:
                from rest_framework.exceptions import NotFound
                raise NotFound('رستوران یافت نشد.')
            
            # بررسی اینکه آیا رستوران به یکی از مراکز Food Admin تعلق دارد یا نه
            user_centers = user.centers.all()
            restaurant_centers = instance.centers.all()
            
            # اگر رستوران به هیچ یک از مراکز Food Admin تعلق ندارد، اجازه ویرایش ندارد
            if not any(center in user_centers for center in restaurant_centers):
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied('شما نمی‌توانید این رستوران را ویرایش کنید. این رستوران به مراکز شما اختصاص داده نشده است.')
            
            # Food Admin می‌تواند مراکز را به مراکز خودش و مراکز دیگر تغییر دهد
            # هیچ محدودیتی برای مراکز جدید اعمال نمی‌کنیم
        
        return super().update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        """حذف رستوران - Food Admin فقط می‌تواند رستوران‌های مراکز خودش را حذف کند"""
        user = request.user
        if user.role == 'admin_food':
            instance = self.get_object()
            # بررسی اینکه رستوران متعلق به یکی از مراکز Food Admin است
            if not instance.centers.filter(id__in=user.centers.values_list('id', flat=True)).exists():
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied('شما نمی‌توانید این رستوران را حذف کنید. این رستوران به مراکز شما اختصاص داده نشده است.')
        
        return super().destroy(request, *args, **kwargs)


# ========== Admin Food Restaurants ==========

@extend_schema(
    operation_id='admin_food_restaurants',
    summary='Get Restaurants for Food Admin',
    description='Get list of restaurants that belong to the food admin\'s centers. Food admin can see all restaurants of their assigned centers. No center parameter needed. Returns simplified restaurant data.',
    tags=['Food Management'],
    responses={200: SimpleRestaurantSerializer(many=True)}
)
@api_view(['GET'])
@permission_classes([IsFoodAdminOrSystemAdmin])
def admin_food_restaurants(request):
    """لیست رستوران‌های مراکز ادمین غذا - خروجی ساده"""
    user = request.user
    
    # بررسی اینکه کاربر ادمین غذا است
    if user.role not in ['admin_food', 'sys_admin']:
        return Response({
            'error': 'دسترسی غیرمجاز'
        }, status=status.HTTP_403_FORBIDDEN)
    
    # اگر sys_admin است، همه رستوران‌ها را برگردان
    if user.role == 'sys_admin':
        restaurants = Restaurant.objects.all()
    else:
        # برای admin_food، فقط رستوران‌های مراکز خودش
        if not user.centers.exists():
            return Response({
                'error': 'کاربر مرکز مشخصی ندارد'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        restaurants = Restaurant.objects.filter(
            centers__in=user.centers.all()
        ).distinct()
    
    # استفاده از serializer ساده
    serializer = SimpleRestaurantSerializer(restaurants, many=True, context={'request': request})
    return Response(serializer.data)


# ========== Admin Food Meals by Date ==========

@extend_schema(
    operation_id='admin_food_meals_by_date',
    summary='Get/Update Meals by Date for Food Admin',
    description='GET/POST: Get list of meals that exist in daily menus for a specific date. Food admin can only see meals of restaurants that belong to their assigned centers. Returns only meal data without restaurant information. No pagination.\n\nPOST: Add or update a single meal with its options in daily menu for a specific date. Requires date, restaurant_id, base_meal_id, and meal_options array (title, description, price, quantity).',
    tags=['Food Management'],
    request=DailyMenuMealUpdateSerializer,
    responses={
        200: SimpleBaseMealSerializer(many=True),
        201: DailyMenuSerializer,
        400: {'description': 'Validation error'},
        403: {'description': 'Permission denied'}
    }
)
@api_view(['POST'])
@permission_classes([IsFoodAdminOrSystemAdmin])
def admin_food_meals_by_date(request):
    """لیست و به‌روزرسانی غذاهای موجود در منو برای یک تاریخ مشخص - برای ادمین غذا
    
    برای دریافت لیست: POST با فیلد date در body
    برای افزودن/ویرایش: POST با فیلدهای date, restaurant_id, base_meal_id, meal_options در body
    """
    user = request.user
    
    # بررسی دسترسی برای افزودن/ویرایش - فقط Food Admin
    if user.role != 'admin_food':
        return Response({
            'error': 'فقط ادمین غذا می‌تواند منو را مدیریت کند'
        }, status=status.HTTP_403_FORBIDDEN)
    
    # دریافت تاریخ از POST body (برای GET و POST هر دو)
    date = request.data.get('date')
    
    # بررسی اینکه تاریخ وجود دارد و خالی نیست
    if not date or (isinstance(date, str) and not date.strip()):
        return Response({
            'error': 'تاریخ الزامی است. لطفاً فیلد date را در request body ارسال کنید.'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # تبدیل به string و strip کردن
    date = str(date).strip()
    
    # تبدیل تاریخ شمسی یا میلادی به فرمت مناسب
    parsed_date = parse_date_filter(date)
    if not parsed_date:
        return Response({
            'error': f'فرمت تاریخ نامعتبر است: "{date}". از فرمت میلادی (2025-10-24) یا شمسی (1404/08/02) استفاده کنید'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # بررسی اینکه آیا برای دریافت لیست است یا افزودن/ویرایش
    restaurant_id = request.data.get('restaurant_id')
    base_meal_id = request.data.get('base_meal_id')
    meal_options_data = request.data.get('meal_options')
    
    # اگر restaurant_id و base_meal_id وجود ندارند، یعنی درخواست دریافت لیست است
    if not restaurant_id and not base_meal_id and not meal_options_data:
        # دریافت لیست غذاها
        # دریافت منوهای روزانه برای آن تاریخ
        if user.role == 'sys_admin':
            # System Admin: همه منوها
            daily_menus = DailyMenu.objects.filter(date=parsed_date, is_available=True)
        else:
            # Food Admin: فقط منوهای رستوران‌های مراکز خود
            if not user.centers.exists():
                return Response({
                    'error': 'کاربر مرکز مشخصی ندارد'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            daily_menus = DailyMenu.objects.filter(
                date=parsed_date,
                is_available=True,
                restaurant__centers__in=user.centers.all()
            ).distinct()
        
        # استخراج base_meal ها از meal_options موجود در منوها - بدون تکرار
        meal_ids = set()
        for daily_menu in daily_menus.select_related('restaurant').prefetch_related('menu_meal_options__base_meal'):
            for meal_option in daily_menu.menu_meal_options.all():
                if meal_option.base_meal:
                    meal_ids.add(meal_option.base_meal.id)
        
        # دریافت غذاها - بدون تکرار و مرتب شده
        if meal_ids:
            meals = Meal.objects.filter(id__in=meal_ids).distinct().order_by('id')
        else:
            meals = Meal.objects.none()
        
        # استفاده از serializer ساده (بدون اطلاعات رستوران)
        serializer = SimpleBaseMealSerializer(meals, many=True, context={'request': request})
        # حذف تکرارها از نتیجه (در صورت وجود)
        seen_ids = set()
        unique_data = []
        for item in serializer.data:
            if item['id'] not in seen_ids:
                seen_ids.add(item['id'])
                unique_data.append(item)
        
        return Response(unique_data)
    
    # افزودن/ویرایش یک غذا در منو - فقط ادمین غذا
    else:
        if user.role != 'admin_food':
            return Response({
                'error': 'فقط ادمین غذا می‌تواند منو را مدیریت کند'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # اعتبارسنجی داده‌ها
        serializer = DailyMenuMealUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        restaurant_id = serializer.validated_data['restaurant_id']
        base_meal_id = serializer.validated_data['base_meal_id']
        meal_options_data = serializer.validated_data['meal_options']
        
        # بررسی دسترسی به رستوران
        try:
            restaurant = Restaurant.objects.get(id=restaurant_id)
        except Restaurant.DoesNotExist:
            return Response({
                'error': 'رستوران یافت نشد'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # بررسی دسترسی ادمین غذا به رستوران
        if not user.centers.exists():
            return Response({
                'error': 'کاربر مرکز مشخصی ندارد'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # بررسی اینکه رستوران به مراکز ادمین غذا متصل است
        restaurant_centers = restaurant.centers.all()
        user_centers = user.centers.all()
        if not any(center in restaurant_centers for center in user_centers):
            return Response({
                'error': 'شما به این رستوران دسترسی ندارید'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # بررسی وجود base_meal
        try:
            base_meal = BaseMeal.objects.get(id=base_meal_id)
        except BaseMeal.DoesNotExist:
            return Response({
                'error': f'غذای پایه با شناسه {base_meal_id} یافت نشد'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # پیدا کردن یا ایجاد DailyMenu
        daily_menu, created = DailyMenu.objects.get_or_create(
            restaurant=restaurant,
            date=parsed_date,
            defaults={'is_available': True}
        )
        
        # اضافه کردن base_meal به base_meals ManyToMany (اگر وجود نداشته باشد)
        daily_menu.base_meals.add(base_meal)
        
        # حذف meal_options قدیمی برای این base_meal در این daily_menu
        DailyMenuMealOption.objects.filter(
            daily_menu=daily_menu,
            base_meal=base_meal
        ).delete()
        
        # ایجاد meal_options جدید
        for option_data in meal_options_data:
            cancellation_deadline = option_data.get('cancellation_deadline')
            # تاریخ به صورت string ذخیره می‌شود (بدون تبدیل)
            if cancellation_deadline:
                cancellation_deadline = str(cancellation_deadline).strip() if cancellation_deadline else None
                if cancellation_deadline == '':
                    cancellation_deadline = None
            
            DailyMenuMealOption.objects.create(
                daily_menu=daily_menu,
                base_meal=base_meal,
                title=option_data['title'],
                description=option_data.get('description', ''),
                price=option_data['price'],
                quantity=option_data['quantity'],
                cancellation_deadline=cancellation_deadline,
                is_default=False,
                sort_order=0
            )
        
        # بارگذاری مجدد daily_menu با تمام روابط
        daily_menu.refresh_from_db()
        daily_menu = DailyMenu.objects.prefetch_related(
            'menu_meal_options__base_meal',
            'restaurant__centers'
        ).get(id=daily_menu.id)
        
        # استفاده از DailyMenuSerializer برای برگرداندن داده‌های کامل
        serializer = DailyMenuSerializer(daily_menu, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)


# ========== Remove Meal from Daily Menu ==========

@extend_schema(
    operation_id='admin_food_remove_meal_from_menu',
    summary='Remove Meal from Daily Menu',
    description='Remove a base meal and all its meal options from daily menu for a specific date. Food admin can only remove meals from restaurants that belong to their assigned centers.',
    tags=['Food Management'],
    parameters=[
        {
            'name': 'date',
            'in': 'query',
            'description': 'Date (format: YYYY-MM-DD or YYYY/MM/DD)',
            'required': True,
            'schema': {'type': 'string'}
        },
        {
            'name': 'restaurant_id',
            'in': 'query',
            'description': 'Restaurant ID',
            'required': True,
            'schema': {'type': 'integer'}
        },
        {
            'name': 'base_meal_id',
            'in': 'query',
            'description': 'Base Meal ID to remove',
            'required': True,
            'schema': {'type': 'integer'}
        }
    ],
    responses={
        200: DailyMenuSerializer,
        400: {'description': 'Validation error'},
        403: {'description': 'Permission denied'},
        404: {'description': 'Not found'}
    }
)
@api_view(['DELETE'])
@permission_classes([IsFoodAdminOrSystemAdmin])
def admin_food_remove_meal_from_menu(request):
    """حذف غذا از منوی روزانه - برای ادمین غذا"""
    user = request.user
    
    # بررسی اینکه کاربر ادمین غذا است
    if user.role not in ['admin_food', 'sys_admin']:
        return Response({
            'error': 'دسترسی غیرمجاز'
        }, status=status.HTTP_403_FORBIDDEN)
    
    # دریافت پارامترها
    date = request.query_params.get('date')
    restaurant_id = request.query_params.get('restaurant_id')
    base_meal_id = request.query_params.get('base_meal_id')
    
    if not date:
        return Response({
            'error': 'تاریخ الزامی است'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    if not restaurant_id:
        return Response({
            'error': 'شناسه رستوران الزامی است'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    if not base_meal_id:
        return Response({
            'error': 'شناسه غذای پایه الزامی است'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # تبدیل تاریخ
    parsed_date = parse_date_filter(date)
    if not parsed_date:
        return Response({
            'error': 'فرمت تاریخ نامعتبر است. از فرمت میلادی (2025-10-24) یا شمسی (1404/08/02) استفاده کنید'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # تبدیل restaurant_id و base_meal_id
    try:
        restaurant_id = int(restaurant_id)
        base_meal_id = int(base_meal_id)
    except (ValueError, TypeError):
        return Response({
            'error': 'شناسه رستوران و غذای پایه باید عدد باشند'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # بررسی وجود رستوران
    try:
        restaurant = Restaurant.objects.get(id=restaurant_id)
    except Restaurant.DoesNotExist:
        return Response({
            'error': 'رستوران یافت نشد'
        }, status=status.HTTP_404_NOT_FOUND)
    
    # بررسی دسترسی ادمین غذا به رستوران
    if not user.centers.exists():
        return Response({
            'error': 'کاربر مرکز مشخصی ندارد'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # بررسی اینکه رستوران به مراکز ادمین غذا متصل است
    restaurant_centers = restaurant.centers.all()
    user_centers = user.centers.all()
    if not any(center in restaurant_centers for center in user_centers):
        return Response({
            'error': 'شما به این رستوران دسترسی ندارید'
        }, status=status.HTTP_403_FORBIDDEN)
    
    # بررسی وجود base_meal
    try:
        base_meal = BaseMeal.objects.get(id=base_meal_id)
    except BaseMeal.DoesNotExist:
        return Response({
            'error': 'غذای پایه یافت نشد'
        }, status=status.HTTP_404_NOT_FOUND)
    
    # پیدا کردن DailyMenu
    try:
        daily_menu = DailyMenu.objects.get(
            restaurant=restaurant,
            date=parsed_date
        )
    except DailyMenu.DoesNotExist:
        return Response({
            'error': 'منوی روزانه برای این تاریخ و رستوران یافت نشد'
        }, status=status.HTTP_404_NOT_FOUND)
    
    # حذف تمام meal_options مربوط به این base_meal
    deleted_count = DailyMenuMealOption.objects.filter(
        daily_menu=daily_menu,
        base_meal=base_meal
    ).delete()[0]
    
    # حذف base_meal از base_meals ManyToMany
    daily_menu.base_meals.remove(base_meal)
    
    # بارگذاری مجدد daily_menu با تمام روابط
    daily_menu.refresh_from_db()
    daily_menu = DailyMenu.objects.prefetch_related(
        'menu_meal_options__base_meal',
        'restaurant__centers'
    ).get(id=daily_menu.id)
    
    # استفاده از DailyMenuSerializer برای برگرداندن داده‌های کامل
    serializer = DailyMenuSerializer(daily_menu, context={'request': request})
    return Response({
        'message': f'غذا و {deleted_count} اپشن آن با موفقیت از منو حذف شد',
        'deleted_meal_options_count': deleted_count,
        'daily_menu': serializer.data
    }, status=status.HTTP_200_OK)


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
                queryset = queryset.filter(restaurant__centers__id=center_id).distinct()
            except (ValueError, TypeError):
                # Invalid center_id, return empty queryset
                queryset = queryset.none()
        elif user.centers.exists() and not user.is_admin:
            queryset = queryset.filter(restaurant__centers__in=user.centers.all()).distinct()
        
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
        
        # بهینه‌سازی با prefetch_related برای جلوگیری از تکرار query ها
        queryset = queryset.select_related('restaurant').prefetch_related(
            'restaurant__centers',
            'menu_meal_options',
            'menu_meal_options__base_meal',
            'menu_dessert_options',
            'menu_dessert_options__base_dessert'
        )
        
        return queryset.order_by('date', 'restaurant__name')


# ========== Dessert Management ==========

@extend_schema_view(
    get=extend_schema(
        operation_id='dessert_list',
        summary='List Desserts',
        description='Get list of all desserts. Desserts are managed per DailyMenu via admin panel.',
        tags=['Desserts']
    ),
    post=extend_schema(
        operation_id='dessert_create',
        summary='Create Dessert',
        description='Create new dessert. After creation, add desserts to daily menu via admin panel when creating/editing a DailyMenu. (only for food admins and system admins). Returns simplified dessert data without restaurant details.',
        tags=['Desserts'],
        request=DessertSerializer,
        responses={
            201: SimpleDessertSerializer,
            400: {'description': 'Validation error'},
            403: {'description': 'Permission denied'}
        }
    )
)
class DessertListCreateView(generics.ListCreateAPIView):
    """لیست و ایجاد دسرها"""
    queryset = Dessert.objects.all()
    serializer_class = DessertSerializer
    permission_classes = [FoodManagementPermission]
    pagination_class = CustomPageNumberPagination

    def get_queryset(self):
        user = self.request.user
        if user.role == 'sys_admin':
            return Dessert.objects.all()
        elif user.role == 'admin_food':
            if user.centers.exists():
                return Dessert.objects.filter(
                    restaurant__centers__in=user.centers.all()
                ).distinct()
            return Dessert.objects.none()
        elif user.centers.exists():
            return Dessert.objects.filter(is_active=True, center__in=user.centers.all())
        return Dessert.objects.none()
    
    def create(self, request, *args, **kwargs):
        user = request.user
        if user.role != 'admin_food':
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("فقط ادمین غذا می‌تواند دسر ایجاد کند")
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        dessert = serializer.save()
        
        response_serializer = SimpleDessertSerializer(dessert, context={'request': request})
        headers = self.get_success_headers(response_serializer.data)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED, headers=headers)


@extend_schema_view(
    get=extend_schema(
        operation_id='dessert_detail',
        summary='Get Dessert Details',
        description='Get dessert details. Returns simplified dessert data without restaurant information.',
        tags=['Desserts'],
        responses={
            200: SimpleDessertSerializer,
            404: {'description': 'Dessert not found'}
        }
    ),
    put=extend_schema(
        operation_id='dessert_update',
        summary='Update Dessert',
        description='Update dessert. Note: Desserts should be managed via admin panel when creating/editing a DailyMenu. (only for admins). Returns simplified dessert data without restaurant information.',
        tags=['Desserts'],
        request=DessertSerializer,
        responses={
            200: SimpleDessertSerializer,
            400: {'description': 'Validation error'},
            403: {'description': 'Permission denied'},
            404: {'description': 'Dessert not found'}
        }
    ),
    patch=extend_schema(
        operation_id='dessert_partial_update',
        summary='Partial Update Dessert',
        description='Partially update dessert. Note: Desserts should be managed via admin panel when creating/editing a DailyMenu. (only for admins). Returns simplified dessert data without restaurant information.',
        tags=['Desserts'],
        request=DessertSerializer,
        responses={
            200: SimpleDessertSerializer,
            400: {'description': 'Validation error'},
            403: {'description': 'Permission denied'},
            404: {'description': 'Dessert not found'}
        }
    ),
    delete=extend_schema(
        operation_id='dessert_delete',
        summary='Delete Dessert',
        description='Delete dessert (only for admins)',
        tags=['Desserts']
    )
)
class DessertDetailView(generics.RetrieveUpdateDestroyAPIView):
    """جزئیات، ویرایش و حذف دسر"""
    queryset = Dessert.objects.all()
    serializer_class = DessertSerializer
    permission_classes = [FoodManagementPermission]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'sys_admin':
            return Dessert.objects.all()
        elif user.role == 'admin_food':
            if user.centers.exists():
                return Dessert.objects.filter(
                    restaurant__centers__in=user.centers.all()
                ).distinct()
            return Dessert.objects.none()
        elif user.centers.exists():
            return Dessert.objects.filter(center__in=user.centers.all())
        else:
            return Dessert.objects.none()
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = SimpleDessertSerializer(instance, context={'request': request})
        return Response(serializer.data)
    
    def update(self, request, *args, **kwargs):
        """به‌روزرسانی دسر - فقط ادمین غذا"""
        user = request.user
        if user.role != 'admin_food':
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("فقط ادمین غذا می‌تواند دسر را ویرایش کند")
        
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        dessert = serializer.save()
        
        response_serializer = SimpleDessertSerializer(dessert, context={'request': request})
        return Response(response_serializer.data)
    
    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        """حذف دسر - فقط ادمین غذا"""
        user = request.user
        if user.role != 'admin_food':
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("فقط ادمین غذا می‌تواند دسر را حذف کند")
        return super().destroy(request, *args, **kwargs)


@extend_schema(
    operation_id='restaurant_desserts',
    summary='Get Desserts by Restaurant',
    description='Get list of desserts for a specific restaurant. Food admin can only see desserts of restaurants that belong to their assigned centers. Returns only dessert data without restaurant information. No pagination.',
    tags=['Desserts'],
    parameters=[
        {
            'name': 'restaurant_id',
            'in': 'path',
            'description': 'ID of the restaurant',
            'required': True,
            'schema': {'type': 'integer'}
        }
    ],
    responses={200: SimpleDessertSerializer(many=True)}
)
@api_view(['GET'])
@permission_classes([FoodManagementPermission])
def restaurant_desserts(request, restaurant_id):
    """دسرهای یک رستوران"""
    try:
        restaurant = Restaurant.objects.get(id=restaurant_id)
    except Restaurant.DoesNotExist:
        return Response({
            'error': 'رستوران یافت نشد'
        }, status=status.HTTP_404_NOT_FOUND)
    
    user = request.user
    
    # بررسی دسترسی
    if user.role == 'sys_admin':
        desserts = Dessert.objects.filter(restaurant=restaurant, is_active=True)
    elif user.role == 'admin_food':
        if user.centers.exists() and restaurant.centers.filter(id__in=user.centers.values_list('id', flat=True)).exists():
            desserts = Dessert.objects.filter(restaurant=restaurant, is_active=True)
        else:
            return Response({
                'error': 'شما دسترسی به این رستوران ندارید'
            }, status=status.HTTP_403_FORBIDDEN)
    else:
        if user.centers.exists() and restaurant.centers.filter(id__in=user.centers.values_list('id', flat=True)).exists():
            desserts = Dessert.objects.filter(restaurant=restaurant, is_active=True)
        else:
            return Response({
                'error': 'شما دسترسی به این رستوران ندارید'
            }, status=status.HTTP_403_FORBIDDEN)
    
    serializer = SimpleDessertSerializer(desserts, many=True, context={'request': request})
    return Response(serializer.data)


@extend_schema(
    operation_id='admin_food_desserts_by_date',
    summary='Get/Update Desserts by Date for Food Admin',
    description='GET/POST: Get list of desserts that exist in daily menus for a specific date. Food admin can only see desserts of restaurants that belong to their assigned centers. Returns only dessert data without restaurant information. No pagination.\n\nPOST: Add or update a single dessert in daily menu for a specific date. Requires date, restaurant_id, dessert_id, title, description, price, quantity.',
    tags=['Food Management'],
    responses={
        200: SimpleDessertSerializer(many=True),
        201: DailyMenuSerializer,
        400: {'description': 'Validation error'},
        403: {'description': 'Permission denied'}
    }
)
@api_view(['POST'])
@permission_classes([IsFoodAdminOrSystemAdmin])
def admin_food_desserts_by_date(request):
    """
    لیست و به‌روزرسانی دسرهای موجود در منو برای یک تاریخ مشخص - برای ادمین غذا
    
    برای دریافت لیست: POST با فیلد date در body
    برای افزودن/ویرایش: POST با فیلدهای date, restaurant_id, dessert_id, title, price در body
    """
    user = request.user
    
    # POST: فقط ادمین غذا می‌تواند منو را مدیریت کند
    if request.method == 'POST' and user.role != 'admin_food':
        return Response({
            'error': 'فقط ادمین غذا می‌تواند منو را مدیریت کند'
        }, status=status.HTTP_403_FORBIDDEN)
    
    # دریافت تاریخ از POST body (برای GET و POST هر دو)
    date = request.data.get('date')
    
    # بررسی اینکه تاریخ وجود دارد و خالی نیست
    if not date or (isinstance(date, str) and not date.strip()):
        return Response({
            'error': 'تاریخ الزامی است. لطفاً فیلد date را در request body ارسال کنید.'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # تبدیل به string و strip کردن
    date = str(date).strip()
    
    # تبدیل تاریخ شمسی یا میلادی به فرمت مناسب
    parsed_date = parse_date_filter(date)
    if not parsed_date:
        return Response({
            'error': f'فرمت تاریخ نامعتبر است: "{date}". از فرمت میلادی (2025-10-24) یا شمسی (1404/08/02) استفاده کنید'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # بررسی اینکه آیا برای دریافت لیست است یا افزودن/ویرایش
    restaurant_id = request.data.get('restaurant_id')
    dessert_id = request.data.get('dessert_id')
    title = request.data.get('title')
    
    # اگر restaurant_id و dessert_id وجود ندارند، یعنی درخواست دریافت لیست است
    if not restaurant_id and not dessert_id and not title:
        # لیست دسرهای موجود در منوهای روزانه برای این تاریخ
        daily_menus = DailyMenu.objects.filter(date=parsed_date)
        
        # فیلتر بر اساس مراکز کاربر
        if user.role == 'admin_food' and user.centers.exists():
            daily_menus = daily_menus.filter(restaurant__centers__in=user.centers.all()).distinct()
        elif user.role == 'sys_admin':
            pass  # System Admin همه منوها را می‌بیند
        
        # استخراج دسرهای منحصر به فرد از منوها
        dessert_ids = []
        for daily_menu in daily_menus:
            dessert_ids.extend(daily_menu.base_desserts.values_list('id', flat=True))
        dessert_ids = list(set(dessert_ids))  # حذف تکرارها
        
        # دریافت دسرها - بدون تکرار و مرتب شده
        if dessert_ids:
            desserts = Dessert.objects.filter(id__in=dessert_ids, is_active=True).distinct().order_by('id')
        else:
            desserts = Dessert.objects.none()
        
        serializer = SimpleDessertSerializer(desserts, many=True, context={'request': request})
        # حذف تکرارها از نتیجه (در صورت وجود)
        seen_ids = set()
        unique_data = []
        for item in serializer.data:
            if item['id'] not in seen_ids:
                seen_ids.add(item['id'])
                unique_data.append(item)
        
        return Response(unique_data)
    
    # افزودن/ویرایش دسر در منو - فقط ادمین غذا
    else:
        # افزودن یا به‌روزرسانی دسر در منوی روزانه
        from apps.food_management.models import BaseDessert, DailyMenuDessertOption
        
        restaurant_id = request.data.get('restaurant_id')
        base_dessert_id = request.data.get('base_dessert_id') or request.data.get('dessert_id')  # برای سازگاری با کد قدیمی
        dessert_options_data = request.data.get('dessert_options', [])
        
        # اگر dessert_options وجود نداشت، از فیلدهای مستقیم استفاده کن (سازگاری با کد قدیمی)
        if not dessert_options_data:
            title = request.data.get('title')
            description = request.data.get('description', '')
            price = request.data.get('price')
            quantity = request.data.get('quantity', 0)
            cancellation_deadline = request.data.get('cancellation_deadline')
            if title and price is not None:
                dessert_options_data = [{
                    'title': title,
                    'description': description,
                    'price': price,
                    'quantity': quantity,
                    'cancellation_deadline': cancellation_deadline
                }]
        
        if not restaurant_id or not base_dessert_id or not dessert_options_data:
            return Response({
                'error': 'restaurant_id, base_dessert_id (یا dessert_id) و dessert_options (یا title, price) الزامی هستند'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            restaurant = Restaurant.objects.get(id=restaurant_id)
        except Restaurant.DoesNotExist:
            return Response({
                'error': 'رستوران یافت نشد'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # بررسی دسترسی ادمین غذا به رستوران
        if not user.centers.exists():
            return Response({
                'error': 'کاربر مرکز مشخصی ندارد'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not restaurant.centers.filter(id__in=user.centers.values_list('id', flat=True)).exists():
            return Response({
                'error': 'شما دسترسی به این رستوران ندارید'
            }, status=status.HTTP_403_FORBIDDEN)
        
        try:
            base_dessert = BaseDessert.objects.get(id=base_dessert_id)
        except BaseDessert.DoesNotExist:
            return Response({
                'error': 'دسر پایه یافت نشد'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # پیدا کردن یا ایجاد DailyMenu
        daily_menu, created = DailyMenu.objects.get_or_create(
            restaurant=restaurant,
            date=parsed_date,
            defaults={'is_available': True}
        )
        
        # اضافه کردن base_dessert به base_desserts ManyToMany (اگر وجود نداشته باشد)
        daily_menu.base_desserts.add(base_dessert)
        
        # حذف dessert_options قدیمی برای این base_dessert در این daily_menu
        DailyMenuDessertOption.objects.filter(
            daily_menu=daily_menu,
            base_dessert=base_dessert
        ).delete()
        
        # ایجاد dessert_options جدید
        for option_data in dessert_options_data:
            cancellation_deadline = option_data.get('cancellation_deadline')
            # تاریخ به صورت string ذخیره می‌شود (بدون تبدیل)
            if cancellation_deadline:
                cancellation_deadline = str(cancellation_deadline).strip() if cancellation_deadline else None
                if cancellation_deadline == '':
                    cancellation_deadline = None
            
            DailyMenuDessertOption.objects.create(
                daily_menu=daily_menu,
                base_dessert=base_dessert,
                title=option_data['title'],
                description=option_data.get('description', ''),
                price=option_data['price'],
                quantity=option_data.get('quantity', 0),
                cancellation_deadline=cancellation_deadline,
                is_default=False,
                sort_order=0
            )
        
        # بارگذاری مجدد daily_menu با تمام روابط
        daily_menu.refresh_from_db()
        daily_menu = DailyMenu.objects.prefetch_related(
            'menu_dessert_options__base_dessert',
            'restaurant__centers'
        ).get(id=daily_menu.id)
        
        serializer = DailyMenuSerializer(daily_menu, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)


@extend_schema(
    operation_id='admin_food_remove_dessert_from_menu',
    summary='Remove Dessert from Daily Menu',
    description='Remove a dessert from daily menu for a specific date. Food admin can only remove desserts from restaurants that belong to their assigned centers.',
    tags=['Food Management'],
    parameters=[
        {
            'name': 'date',
            'in': 'query',
            'description': 'Date (format: YYYY-MM-DD or YYYY/MM/DD)',
            'required': True,
            'schema': {'type': 'string'}
        },
        {
            'name': 'restaurant_id',
            'in': 'query',
            'description': 'Restaurant ID',
            'required': True,
            'schema': {'type': 'integer'}
        },
        {
            'name': 'base_dessert_id',
            'in': 'query',
            'description': 'Base Dessert ID to remove',
            'required': True,
            'schema': {'type': 'integer'}
        }
    ],
    responses={
        200: DailyMenuSerializer,
        400: {'description': 'Validation error'},
        403: {'description': 'Permission denied'},
        404: {'description': 'Not found'}
    }
)
@api_view(['DELETE'])
@permission_classes([IsFoodAdminOrSystemAdmin])
def admin_food_remove_dessert_from_menu(request):
    """حذف دسر از منوی روزانه - فقط ادمین غذا"""
    user = request.user
    
    # فقط ادمین غذا می‌تواند دسر را از منو حذف کند
    if user.role != 'admin_food':
        return Response({
            'error': 'فقط ادمین غذا می‌تواند دسر را از منو حذف کند'
        }, status=status.HTTP_403_FORBIDDEN)
    
    from apps.food_management.models import BaseDessert, DailyMenuDessertOption
    
    date = request.query_params.get('date')
    restaurant_id = request.query_params.get('restaurant_id')
    base_dessert_id = request.query_params.get('base_dessert_id') or request.query_params.get('dessert_id')  # برای سازگاری با کد قدیمی
    
    if not date or not restaurant_id or not base_dessert_id:
        return Response({
            'error': 'date، restaurant_id و base_dessert_id (یا dessert_id) الزامی هستند'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    parsed_date = parse_date_filter(date)
    if not parsed_date:
        return Response({
            'error': 'فرمت تاریخ نامعتبر است'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        restaurant = Restaurant.objects.get(id=restaurant_id)
    except Restaurant.DoesNotExist:
        return Response({
            'error': 'رستوران یافت نشد'
        }, status=status.HTTP_404_NOT_FOUND)
    
    # بررسی دسترسی
    if user.role == 'admin_food' and user.centers.exists():
        if not restaurant.centers.filter(id__in=user.centers.values_list('id', flat=True)).exists():
            return Response({
                'error': 'شما دسترسی به این رستوران ندارید'
            }, status=status.HTTP_403_FORBIDDEN)
    
    try:
        base_dessert = BaseDessert.objects.get(id=base_dessert_id)
    except BaseDessert.DoesNotExist:
        return Response({
            'error': 'دسر پایه یافت نشد'
        }, status=status.HTTP_404_NOT_FOUND)
    
    try:
        daily_menu = DailyMenu.objects.get(restaurant=restaurant, date=parsed_date)
    except DailyMenu.DoesNotExist:
        return Response({
            'error': 'منوی روزانه یافت نشد'
        }, status=status.HTTP_404_NOT_FOUND)
    
    # حذف dessert_options برای این base_dessert در این daily_menu
    DailyMenuDessertOption.objects.filter(
        daily_menu=daily_menu,
        base_dessert=base_dessert
    ).delete()
    
    # حذف base_dessert از ManyToMany
    daily_menu.base_desserts.remove(base_dessert)
    
    # بارگذاری مجدد daily_menu
    daily_menu.refresh_from_db()
    daily_menu = DailyMenu.objects.prefetch_related(
        'menu_dessert_options__base_dessert',
        'restaurant__centers'
    ).get(id=daily_menu.id)
    
    serializer = DailyMenuSerializer(daily_menu, context={'request': request})
    return Response({
        'message': f'دسر با موفقیت از منو حذف شد',
        'daily_menu': serializer.data
    }, status=status.HTTP_200_OK)




@extend_schema(
    operation_id='admin_food_forget_reservations',
    summary='Manage forget reservations for employees',
    description='''
    Food admin can create and view forget reservations for employees.
    A forget reservation is created when an employee forgets to reserve their meal.
    This endpoint allows:
    1. GET: List all forget reservations for a specific employee with filtering options
    2. POST: Create a new forget reservation for an employee
    
    Validations:
    - Only food admin can access this endpoint
    - User cannot have existing reservations (food or dessert) for the same daily menu
    - All required fields must be provided
    - Daily menu and options must exist
    ''',
    tags=[' forget reservation - Food Admin'],
    parameters=[
        OpenApiParameter(
            name='pk',
            description='Employee user ID',
            required=True,
            type=OpenApiTypes.INT,
            location=OpenApiParameter.PATH
        ),
        OpenApiParameter(
            name='date',
            description='Filter reservations by date (format: YYYY-MM-DD)',
            required=False,
            type=OpenApiTypes.DATE,
            location=OpenApiParameter.QUERY
        ),
        OpenApiParameter(
            name='status',
            description='Filter reservations by status',
            required=False,
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            enum=['reserved', 'delivered', 'forgotten', 'cancelled']
        )
    ],
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'daily_menu': {'type': 'integer', 'description': 'Daily menu ID'},
                'meal_option': {'type': 'integer', 'description': 'Meal option ID'},
                'quantity': {'type': 'integer', 'description': 'Number of meals'},
                'base_dessert': {'type': 'boolean', 'description': 'Include base dessert'},
                'dessert_option': {'type': 'integer', 'description': 'Dessert option ID (if base_dessert is true)'}
            },
            'required': ['daily_menu', 'meal_option', 'quantity']
        }
    },
    responses={
        200: OpenApiResponse(
            description='List of forget reservations',
            response=SimpleFoodReservationSerializer(many=True)
        ),
        201: OpenApiResponse(
            description='Forget reservation created successfully',
            response=SimpleFoodReservationSerializer
        ),
        400: OpenApiResponse(
            description='Validation error or user already has reservation'
        ),
        403: OpenApiResponse(
            description='Permission denied - only food admin can access'
        ),
        404: OpenApiResponse(
            description='User, daily menu, or option not found'
        ),
        500: OpenApiResponse(
            description='Internal server error'
        )
    }
)
@api_view(['GET', 'POST'])
@permission_classes([IsFoodAdminOrSystemAdmin])
def admin_food_forget_reservations(request, pk):
    """ثبت رزرو فراموشی از منوی روزانه - فقط ادمین غذا"""
    user = request.user
    
    # فقط ادمین غذا می‌تواند رزرو فراموشی انجام دهد
    if user.role != 'admin_food':
        return Response({
            'error': 'فقط ادمین غذا می‌تواند رزرو فراموشی انجام دهد'
        }, status=status.HTTP_403_FORBIDDEN)
    
    try:
        employee = User.objects.get(pk=pk)
    except User.DoesNotExist:
        return Response({
            'error': 'کاربر مورد نظر یافت نشد'
        }, status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        # لیست رزروها
        reservations = FoodReservation.objects.filter(user=employee).order_by('-reservation_date')
        
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
    
    elif request.method == "POST":
        try:
            data = request.data
            
            # اعتبارسنجی فیلدهای اجباری
            required_fields = ['daily_menu', 'meal_option', 'quantity']
            for field in required_fields:
                if field not in data or not data[field]:
                    return Response({
                        'error': f'فیلد {field} الزامی است'
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            # دریافت داده‌ها
            daily_menu_id = data.get('daily_menu')
            meal_option_id = data.get('meal_option')
            quantity = data.get('quantity')
            base_dessert = data.get('base_dessert')
            dessert_option_id = data.get('dessert_option')
     
            
            # بررسی موجودیت DailyMenu
            try:
                daily_menu = DailyMenu.objects.get(id=daily_menu_id)
            except DailyMenu.DoesNotExist:
                return Response({
                    'error': 'منوی روزانه مورد نظر یافت نشد'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # بررسی موجودیت MealOption
            try:
                meal_option = DailyMenuMealOption.objects.get(id=meal_option_id)
            except DailyMenuMealOption.DoesNotExist:
                return Response({
                    'error': 'گزینه غذایی مورد نظر یافت نشد'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # بررسی DessertOption اگر وجود داشته باشد
            dessert_option = None
            if dessert_option_id:
                try:
                    dessert_option = DailyMenuDessertOption.objects.get(id=dessert_option_id)
                except DailyMenuDessertOption.DoesNotExist:
                    return Response({
                        'error': 'گزینه دسر مورد نظر یافت نشد'
                    }, status=status.HTTP_404_NOT_FOUND)
            
            # بررسی اینکه آیا کاربر قبلاً برای این منو رزرو داشته یا نه
            existing_reservation = FoodReservation.objects.filter(
                user=employee,
                daily_menu=daily_menu,
                status__in=['reserved', 'delivered', 'forgotten']
            ).first()
            
            if existing_reservation:
                return Response({
                    'error': 'این کاربر قبلاً برای این منو رزرو داشته است',
                    'existing_reservation': SimpleFoodReservationSerializer(existing_reservation).data
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # محاسبه مبلغ
            try:
                meal_price = meal_option.price
                dessert_price = dessert_option.price if dessert_option else 0
                amount = (meal_price + dessert_price) * int(quantity)
            except (ValueError, AttributeError) as e:
                return Response({
                    'error': 'خطا در محاسبه مبلغ'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # ایجاد رزرو فراموشی
            reservation = FoodReservation.objects.create(
                user=employee,
                daily_menu=daily_menu,
                meal_option=meal_option,
                quantity=int(quantity),
                amount=amount,
                status='forgotten',  # وضعیت فراموشی
 
 
                 
            )
            dessert_reservation = DessertReservation.objects.create(
                user=employee,
                daily_menu=daily_menu,
                dessert_option=dessert_option,
                quantity=int(quantity),
                amount=dessert_option.price,
                status='forgotten',  # وضعیت فراموشی
 
            )
            
            
 
            
            serializer = FoodReservationSerializer(reservation)
            return Response({
                'message': 'رزرو فراموشی با موفقیت ثبت شد',
                'data': serializer.data
            }, status=status.HTTP_201_CREATED)
            
        except ValueError as e:
            return Response({
                'error': 'مقادیر ورودی نامعتبر است'
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'error': f'خطا در ثبت رزرو: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

      