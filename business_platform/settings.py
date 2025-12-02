"""
Django settings for integrated business platform project.
"""

import os
from pathlib import Path
from decouple import config
from datetime import datetime

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Application Version
APP_VERSION = '1.2.0'
APP_VERSION_DATE = '2025-11-17 16:45'  # Update this when version changes

# Security
SECRET_KEY = config('SECRET_KEY', default='django-insecure-change-this-in-production-123456789')
DEBUG = config('DEBUG', default=True, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1,0.0.0.0,*').split(',')

# CSRF Trusted Origins - for cross-origin requests
csrf_origins = config('CSRF_TRUSTED_ORIGINS', default='')
CSRF_TRUSTED_ORIGINS = [origin.strip() for origin in csrf_origins.split(',') if origin.strip()]

# SSO Configuration
SSO_SECRET_KEY = config('SSO_SECRET_KEY', default=SECRET_KEY)
SSO_ALGORITHM = config('SSO_ALGORITHM', default='HS256')
SSO_TOKEN_LIFETIME = config('SSO_TOKEN_LIFETIME', default=3600, cast=int)  # 1 hour
SSO_REFRESH_LIFETIME = config('SSO_REFRESH_LIFETIME', default=86400, cast=int)  # 24 hours

# Application definition
DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
]

THIRD_PARTY_APPS = [
    'rest_framework',
    'corsheaders',
    'crispy_forms',
    'crispy_bootstrap5',
    'widget_tweaks',
    'django_extensions',
    'django_filters',
]

LOCAL_APPS = [
    # Core platform apps
    'authentication',
    'dashboard',
    'admin_panel',
    'sso',  # Single Sign-On module
    'apps.app_registry',  # Centralized app registry
    # Expense Claim System Apps (expense_accounts disabled due to user model conflict)
    'expense_claims',
    # 'expense_accounts',  # Disabled - has conflicting User model
    'expense_documents',
    'expense_reports',
    # Quotation System
    'quotations',
    # Asset Tracking System
    'assets',
    'locations',
    'movements',
    # Project & Event Management
    'project_management',
    'event_management',
    # Attendance Integration
    'attendance_integration',
    # Leave Management System
    'leave_management',
    # Attendance Systems
    'attendance',  # Basic attendance tracking
    'qr_attendance',  # QR code-based event attendance
    # CRM System
    'crm',  # Customer Relationship Management
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # For static files in production
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',  # Language selection middleware
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'sso.middleware.SSOEnforcementMiddleware',  # Enforce SSO authentication on all requests
    'authentication.middleware.MaintenanceModeMiddleware',  # Check for maintenance mode
    'authentication.middleware.PasswordChangeRequiredMiddleware',  # Force password change on first login
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# SSO Enforcement Configuration
# Set to False to disable SSO enforcement during development
SSO_ENFORCE = config('SSO_ENFORCE', default=True, cast=bool)

ROOT_URLCONF = 'business_platform.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'business_platform.context_processors.app_context',  # App version and global settings
            ],
        },
    },
]

WSGI_APPLICATION = 'business_platform.wsgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME', default='business_platform_db'),
        'USER': config('DB_USER', default='postgres'),
        'PASSWORD': config('DB_PASSWORD', default='postgres'),
        'HOST': config('DB_HOST', default='localhost'),
        'PORT': config('DB_PORT', default='5432'),
    }
}

# Fallback to SQLite for development
if config('USE_SQLITE', default=False, cast=bool):
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

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
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Supported languages
LANGUAGES = [
    ('en', 'English'),
    ('zh-hans', '简体中文'),  # Simplified Chinese
]

# Locale paths for translation files
LOCALE_PATHS = [
    BASE_DIR / 'locale',
    BASE_DIR / 'project_management' / 'locale',
]

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Custom User Model
AUTH_USER_MODEL = 'authentication.CompanyUser'  # Use authentication CompanyUser model

# REST Framework configuration
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}

# CORS settings
CORS_ALLOW_ALL_ORIGINS = DEBUG
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

# Cache time to live settings (for CRM and other apps)
CACHE_TTL = {
    'customer_list': 60 * 2,  # 2 minutes
    'customer_search': 60 * 5,  # 5 minutes
    'course_list': 60 * 10,  # 10 minutes
    'country_codes': 60 * 60 * 24,  # 24 hours
    'dashboard_stats': 60 * 5,  # 5 minutes
    'api_responses': 60 * 3,  # 3 minutes
    'query_cache': 60 * 1,  # 1 minute
}

# Crispy Forms
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

# Login/Logout URLs
LOGIN_URL = '/auth/login/'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/'

# Session settings
SESSION_COOKIE_AGE = 86400  # 24 hours
SESSION_SAVE_EVERY_REQUEST = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = False

# App Integration Settings - Fixed paths for each business application
BUSINESS_APPS = {
    'leave_system': {
        'name': 'Leave Management System',
        'description': 'Manage employee leave requests and approvals',
        'path': '/apps/leave/',
        'icon': 'fas fa-calendar-alt',
        'color': '#28a745',
        'internal_port': 8001,
        'app_root': '../company-leave-system/',
    },
    'quotation_system': {
        'name': 'Cost Quotation System',
        'description': 'Create and manage cost quotations',
        'path': '/apps/quotations/',
        'icon': 'fas fa-calculator',
        'color': '#007bff',
        'internal_port': 8002,
        'app_root': '../company-cost-quotation-system/',
    },
    'expense_system': {
        'name': 'Expense Claim System',
        'description': 'Submit and track expense claims',
        'path': '/apps/expenses/',
        'icon': 'fas fa-receipt',
        'color': '#dc3545',
        'internal_port': 8003,
        'app_root': '../company_expense_claim_system/',
    },
    'crm_system': {
        'name': 'CRM System',
        'description': 'Customer relationship management',
        'path': '/apps/crm/',
        'icon': 'fas fa-users',
        'color': '#6f42c1',
        'internal_port': 8004,
        'app_root': '../company_crm_system/crm_project/',
    },
    'asset_management': {
        'name': 'Asset Movement Tracking System',
        'description': 'Track and manage company asset movements',
        'path': '/apps/assets/',
        'icon': 'fas fa-boxes',
        'color': '#fd7e14',
        'internal_port': 8005,
        'app_root': '../asset-movement-tracking-system/',
    },
    'stripe_dashboard': {
        'name': 'Stripe Dashboard',
        'description': 'Payment processing and financial reports',
        'path': '/apps/stripe/',
        'icon': 'fab fa-stripe-s',
        'color': '#635bff',
        'internal_port': 8006,
        'app_root': '../stripe-dashboard/',
    },
    'attendance_system': {
        'name': 'Attendance System',
        'description': 'WiFi-based attendance tracking with auto clock-in/out',
        'path': '/apps/attendance/',
        'icon': 'fas fa-clock',
        'color': '#20c997',
        'internal_port': 8007,
        'app_root': '../attendance-system/',
    },
}

# Attendance System Configuration
ATTENDANCE_API_URL = 'http://localhost:8007'

# Security settings - force disable SSL redirect for local development
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# Security settings for production
if not DEBUG:
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_HSTS_SECONDS = 31536000  # 1 year
    X_FRAME_OPTIONS = 'DENY'
    SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'

# Logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# Create logs directory if DEBUG is False
if not DEBUG:
    os.makedirs(BASE_DIR / 'logs', exist_ok=True)
    LOGGING['handlers']['file'] = {
        'level': 'INFO',
        'class': 'logging.FileHandler',
        'filename': BASE_DIR / 'logs' / 'django.log',
        'formatter': 'verbose',
    }
    LOGGING['root']['handlers'].append('file')
    LOGGING['loggers']['django']['handlers'].append('file')