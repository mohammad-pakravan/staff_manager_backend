from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from rest_framework.exceptions import PermissionDenied
from drf_spectacular.utils import extend_schema, extend_schema_view
from drf_spectacular.types import OpenApiTypes
from .models import User
from .serializers import UserSerializer, UserRegistrationSerializer, LoginSerializer, LoginResponseSerializer


@extend_schema(
    summary='Refresh Token',
    description='ایجاد access token جدید با استفاده از refresh token از HttpOnly cookie. نیازی به ارسال body نیست.',
    tags=['Authentication'],
    request=None,
    responses={
        200: {
            'description': 'Token جدید ایجاد شد',
            'content': {
                'application/json': {
                    'example': {
                        'message': 'Token جدید ایجاد شد'
                    }
                }
            }
        },
        400: {
            'description': 'Refresh token یافت نشد یا نامعتبر است',
            'content': {
                'application/json': {
                    'example': {
                        'error': 'Refresh token یافت نشد'
                    }
                }
            }
        }
    }
)
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def refresh_token_view(request):
    """Refresh token با استفاده از HttpOnly cookie"""
    # دریافت refresh token از cookie
    refresh_token = request.COOKIES.get('refresh_token')
    
    if not refresh_token:
        return Response(
            {'error': 'Refresh token یافت نشد'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        refresh = RefreshToken(refresh_token)
        access_token = str(refresh.access_token)
        
        # ساخت Response
        response = Response({
            'message': 'Token جدید ایجاد شد'
        })
        
        # تنظیم access token جدید در HttpOnly cookie
        from django.conf import settings
        cookie_samesite = 'Lax'  # برای development با proxy
        
        response.set_cookie(
            key='access_token',
            value=access_token,
            httponly=True,
            secure=False,
            samesite=cookie_samesite,
            max_age=60 * 60,  # 1 ساعت
            path='/'
        )
        
        # اگر refresh token rotate شود، آن را هم بروزرسانی می‌کنیم
        if refresh:
            response.set_cookie(
                key='refresh_token',
                value=str(refresh),
                httponly=True,
                secure=False,
                samesite=cookie_samesite,
                max_age=7 * 24 * 60 * 60,  # 7 روز
                path='/'
            )
        
        return response
    except Exception as e:
        return Response(
            {'error': 'Token نامعتبر است'},
            status=status.HTTP_400_BAD_REQUEST
        )


 

@extend_schema(
    summary='Login',
    description='لاگین با HttpOnly cookies برای امنیت بیشتر. توکن‌ها در HttpOnly cookies قرار می‌گیرند.',
    tags=['Authentication'],
    request=LoginSerializer,
    responses={
        200: {
            'description': 'لاگین موفق',
            'content': {
                'application/json': {
                    'example': {
                        'user': {
                            'id': 1,
                            'username': 'admin',
                            'email': 'admin@example.com',
                            'first_name': 'محمد',
                            'last_name': 'پاکروان',
                            'role': 'sys_admin',
                            'role_display': 'System Admin'
                        },
                        'message': 'لاگین با موفقیت انجام شد',
                        'note': 'Tokens are stored in HttpOnly cookies and sent automatically with each request'
                    }
                }
            }
        },
        400: {'description': 'ورودی نامعتبر یا اطلاعات اشتباه'}
    }
)
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def login_view(request):
    """
    لاگین با HttpOnly cookies برای امنیت بیشتر
    
    توکن‌ها در HttpOnly cookies قرار می‌گیرند و در response body برگردانده نمی‌شوند.
    برای استفاده در Frontend مرورگر، cookies به صورت خودکار ارسال می‌شوند.
    """
    serializer = LoginSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.validated_data['user']
        refresh = RefreshToken.for_user(user)
        
        # ساخت Response - توکن‌ها در cookies هستند، نه در response body
        response = Response({
            'user': LoginResponseSerializer(user).data,
            'message': 'لاگین با موفقیت انجام شد',
            'note': 'Tokens are stored in HttpOnly cookies and sent automatically with each request'
        })
        
        # تنظیم access token در HttpOnly cookie
        from django.conf import settings
        is_development = settings.DEBUG
        
        # در development، از Lax استفاده می‌کنیم (برای proxy)
        # در production، از Lax یا None با secure=True استفاده می‌کنیم
        cookie_samesite = 'Lax'  # برای development با proxy
        
        response.set_cookie(
            key='access_token',
            value=str(refresh.access_token),
            httponly=True,  # JavaScript نمی‌تواند به آن دسترسی داشته باشد
            secure=False,  # در production باید True باشد (HTTPS)
            samesite=cookie_samesite,
            max_age=60 * 60,  # 1 ساعت (مطابق با ACCESS_TOKEN_LIFETIME)
            path='/'
        )
        
        # تنظیم refresh token در HttpOnly cookie
        response.set_cookie(
            key='refresh_token',
            value=str(refresh),
            httponly=True,
            secure=False,  # در production باید True باشد
            samesite=cookie_samesite,
            max_age=7 * 24 * 60 * 60,  # 7 روز (مطابق با REFRESH_TOKEN_LIFETIME)
            path='/'
        )
        
        return response
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    summary='Get Current User',
    description='دریافت اطلاعات کاربر فعلی',
    tags=['Authentication'],
    responses={
        200: UserSerializer,
        401: {'description': 'Unauthorized'}
    }
)
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def me_view(request):
    serializer = UserSerializer(request.user)
    return Response(serializer.data)


@extend_schema(
    summary='Logout',
    description='لاگ اوت با پاک کردن HttpOnly cookies',
    tags=['Authentication'],
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'refresh': {
                    'type': 'string',
                    'description': 'Refresh token (optional, can be from cookie)',
                    'required': False
                }
            }
        }
    },
    responses={
        200: {
            'description': 'لاگ اوت موفق',
            'content': {
                'application/json': {
                    'example': {
                        'message': 'با موفقیت خارج شدید.'
                    }
                }
            }
        }
    }
)
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def logout_view(request):
    """لاگ اوت با پاک کردن HttpOnly cookies"""
    try:
        # دریافت refresh token از cookie یا request body
        refresh_token = request.COOKIES.get('refresh_token') or request.data.get('refresh')
        
        if refresh_token:
            token = RefreshToken(refresh_token)
            token.blacklist()
        
        # ساخت Response
        response = Response({'message': 'با موفقیت خارج شدید.'})
        
        # پاک کردن cookies
        response.delete_cookie('access_token', path='/')
        response.delete_cookie('refresh_token', path='/')
        
        return response
    except Exception as e:
        # حتی اگر token معتبر نباشد، cookies را پاک می‌کنیم
        response = Response({'message': 'با موفقیت خارج شدید.'})
        response.delete_cookie('access_token', path='/')
        response.delete_cookie('refresh_token', path='/')
        return response


@extend_schema_view(
    get=extend_schema(
        summary='List Users',
        description='لیست کاربران سیستم (فقط برای System Admin)',
        tags=['Users'],
        responses={200: UserSerializer(many=True)}
    ),
    post=extend_schema(
        summary='Create User',
        description='ایجاد کاربر جدید و تخصیص مراکز (فقط برای System Admin)',
        tags=['Users'],
        request=UserRegistrationSerializer,
        responses={
            201: UserSerializer,
            400: {'description': 'Validation error'},
            403: {'description': 'Permission denied'}
        }
    )
)
class UserListCreateView(generics.ListCreateAPIView):
    queryset = User.objects.all().prefetch_related('centers')
    permission_classes = [permissions.IsAuthenticated]

    def _ensure_sys_admin(self, user):
        if user.role != User.Role.SYS_ADMIN:
            raise PermissionDenied('Only System Admin can manage users.')

    def get_queryset(self):
        user = self.request.user
        
        if user.role == 'sys_admin':
            return User.objects.all().prefetch_related('centers')
        
        if user.role in ['hr', 'admin_food']:
            user_centers = user.centers.all()
            return User.objects.filter(
                centers__in=user_centers,
                is_active=True
            ).distinct().prefetch_related('centers')
        
        raise PermissionDenied('دسترسی ندارید')

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return UserRegistrationSerializer
        return UserSerializer

    def create(self, request, *args, **kwargs):
        self._ensure_sys_admin(request.user)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        output_serializer = UserSerializer(user, context=self.get_serializer_context())
        headers = self.get_success_headers(output_serializer.data)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED, headers=headers)