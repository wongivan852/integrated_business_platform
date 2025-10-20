"""
Django settings for integrated business platform project.
"""

import os
from pathlib import Path
from decouple import config

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Security
SECRET_KEY = config('SECRET_KEY', default='django-insecure-change-this-in-production-123456789')
DEBUG = config('DEBUG', default=True, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1,0.0.0.0,*').split(',')

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
    # Core platform apps (root level)
    'core',
    'authentication',
    'dashboard',
    'sso',  # Single Sign-On system
    'admin_panel',  # Admin panel for user and app access management
    'attendance_integration.apps.AttendanceIntegrationConfig',  # Attendance system integration
    # App integrations (in apps/ directory)
    'apps.app_integrations',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # For static files in production
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    # 'business_platform.middleware.AppAccessMiddleware',  # TODO: Create custom middleware for app access control
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

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
                # 'business_platform.context_processors.app_context',  # TODO: Create context processor
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
}

# Security settings - force disable SSL redirect for local development
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# SSO Configuration
SSO_SECRET_KEY = config('SSO_SECRET_KEY', default=SECRET_KEY)
SSO_ALGORITHM = 'HS256'
SSO_TOKEN_LIFETIME = 3600  # 1 hour
SSO_REFRESH_LIFETIME = 86400  # 24 hours

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
# ============================================================================
# ATTENDANCE SYSTEM INTEGRATION
# ============================================================================
# Automatic attendance tracking when users login/logout
ATTENDANCE_INTEGRATION_ENABLED = config('ATTENDANCE_INTEGRATION_ENABLED', default=True, cast=bool)
ATTENDANCE_API_URL = config('ATTENDANCE_API_URL', default='http://localhost:8007')
ATTENDANCE_DEFAULT_PASSWORD = config('ATTENDANCE_DEFAULT_PASSWORD', default='krystal2025')
