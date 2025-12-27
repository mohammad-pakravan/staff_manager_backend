import os
from pathlib import Path
from decouple import config

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY', default='django-insecure-change-me-in-production')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=True, cast=bool)

ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1', cast=lambda v: [s.strip() for s in v.split(',')])

# Application definition
DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

THIRD_PARTY_APPS = [
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'drf_spectacular',
    'jalali_date',
    'webpush',
]

LOCAL_APPS = [
    'apps.accounts',
    'apps.centers',
    'apps.food_management.apps.FoodManagementConfig',  # استفاده از FoodManagementConfig برای ثبت signals
    'apps.meals',
    'apps.reservations',
    'apps.reports',
    'apps.hr.apps.HrConfig',  # استفاده از HrConfig برای ثبت signals
    'apps.core',
    'apps.notifications',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'core.wsgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME', default='staff_db'),
        'USER': config('DB_USER', default='staff_user'),
        'PASSWORD': config('DB_PASSWORD', default='staff_pass'),
        'HOST': config('DB_HOST', default='localhost'),
        'PORT': config('DB_PORT', default='5432'),
    }
}

# Custom User Model
AUTH_USER_MODEL = 'accounts.User'

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Tehran'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# REST Framework configuration
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'apps.accounts.authentication.CookieJWTAuthentication',
        # JWTAuthentication حذف شد چون CookieJWTAuthentication هم از header و هم از cookie پشتیبانی می‌کند
    ),
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_PAGINATION_CLASS': 'apps.core.pagination.CustomPageNumberPagination',
    'PAGE_SIZE': 20,
    'PAGE_SIZE_QUERY_PARAM': 'page_size',
    'MAX_PAGE_SIZE': 100,
}

# Spectacular settings for API documentation
SPECTACULAR_SETTINGS = {
    'TITLE': 'Staff Management System API',
    'DESCRIPTION': "Complete API documentation for Staff Management System including User Management, Food Management, and HR Management",
    'VERSION': '9.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'COMPONENT_SPLIT_REQUEST': True,
    'SCHEMA_PATH_PREFIX': '/api/',
    'SWAGGER_UI_SETTINGS': {
        'deepLinking': True,
        'persistAuthorization': True,
        'displayOperationId': False,
        'defaultModelsExpandDepth': 1,
        'defaultModelExpandDepth': 1,
        'displayRequestDuration': True,
        'docExpansion': 'none',
        'filter': True,
        'showExtensions': True,
        'showCommonExtensions': True,
        'tryItOutEnabled': True,
        'requestSnippetsEnabled': True,
        'requestSnippets': {
            'generators': {
                'curl_bash': {
                    'title': 'cURL (bash)',
                },
                'curl_powershell': {
                    'title': 'cURL (PowerShell)',
                },
            },
        },
        'withCredentials': True,  # برای ارسال cookies در Swagger UI
    },
    'TAGS': [
        {'name': 'Authentication', 'description': 'User authentication and authorization'},
        {'name': 'Centers', 'description': 'Center management operations (System Admin only)'},
        {'name': 'Meals', 'description': 'Base meal management operations (Food Admin & System Admin)'},
        {'name': 'Food Management', 'description': 'Food management endpoints including restaurants, base meals, daily menus, and meal options (DailyMenuMealOption) (Food Admin & System Admin)'},
        {'name': 'Reservations', 'description': 'Food reservation operations'},
        {'name': 'Guest Reservations', 'description': 'Guest reservation operations'},
        {'name': 'User Reservations', 'description': 'User personal and guest reservations'},
        {'name': 'Employee Management', 'description': 'Employee food and guest reservation management (Employee only)'},
        {'name': 'HR', 'description': 'Human Resources and announcements (HR Admin & System Admin only)'},
        {'name': 'Statistics', 'description': 'Comprehensive statistics with filters by date, center, and user (Food Admin, System Admin, HR Admin - read-only)'},
        {'name': 'Reports', 'description': 'Detailed food reservation reports (Food Admin & System Admin only)'},
        {'name': 'Notifications', 'description': 'Push notification subscription management'},
        {'name': 'Server', 'description': 'Server information and time'},
    ],
    'SERVERS': [
        {'url': 'http://localhost:14532', 'description': 'Development server'},
        {'url': 'http://127.0.0.1:8000', 'description': 'Local development server'},
        {'url': 'https://example.com', 'description': 'Production server'},
    ],
    'CONTACT': {
        'name': 'Development Team',
        'email': 'https://t.me/mpakffs',
    },
 
}

# Jalali Date Settings
JALALI_DATE_DEFAULTS = {
    'LIST_DISPLAY_AUTO_CONVERT': True,
    'Strftime': {
        'date': '%Y/%m/%d',
        'datetime': '%Y/%m/%d %H:%M',
    },
    'Static': {
        'js': [
            'admin/js/django_jalali.min.js',
        ],
        'css': {
            'all': [
                'admin/css/django_jalali.min.css',
            ]
        }
    },
}

# CORS settings
CORS_ALLOWED_ORIGINS = config(
    'CORS_ALLOWED_ORIGINS',
    default='http://localhost:3000,http://127.0.0.1:3000,http://localhost:8000,http://127.0.0.1:8000,http://localhost:14532,http://127.0.0.1:14532',
    cast=lambda v: [s.strip() for s in v.split(',')]
)

CORS_ALLOW_CREDENTIALS = True

# CORS settings for Swagger UI
CORS_ALLOW_ALL_ORIGINS = config('CORS_ALLOW_ALL_ORIGINS', default=False, cast=bool)  # فقط برای development

# JWT Settings
from datetime import timedelta

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    'AUDIENCE': None,
    'ISSUER': None,
    'JWK_URL': None,
    'LEEWAY': 0,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'USER_AUTHENTICATION_RULE': 'rest_framework_simplejwt.authentication.default_user_authentication_rule',
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
    'JTI_CLAIM': 'jti',
    'SLIDING_TOKEN_REFRESH_EXP_CLAIM': 'refresh_exp',
    'SLIDING_TOKEN_LIFETIME': timedelta(minutes=5),
    'SLIDING_TOKEN_REFRESH_LIFETIME': timedelta(days=1),
}

# WebPush Settings
WEBPUSH_SETTINGS = {
    "VAPID_PUBLIC_KEY": config('VAPID_PUBLIC_KEY', default=''),
    "VAPID_PRIVATE_KEY": config('VAPID_PRIVATE_KEY', default=''),
    "VAPID_ADMIN_EMAIL": config('VAPID_ADMIN_EMAIL', default='admin@example.com'),
}
