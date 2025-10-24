from .base import *
import tempfile
import os

# Test settings
DEBUG = True

# Use in-memory SQLite for tests
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# Use migrations for tests
# MIGRATION_MODULES = DisableMigrations()

# Media files for tests
MEDIA_ROOT = tempfile.mkdtemp()

# Password hashing for tests (faster)
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# Disable logging during tests
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'null': {
            'class': 'logging.NullHandler',
        },
    },
    'root': {
        'handlers': ['null'],
    },
}

# Test email backend
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

# Disable cache during tests
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

# Test-specific settings
SECRET_KEY = 'test-secret-key'
ALLOWED_HOSTS = ['testserver']

# Disable CORS for tests
CORS_ALLOW_ALL_ORIGINS = True
