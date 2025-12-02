"""
URL configuration for business_platform project.
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView
from django.views.i18n import set_language
from authentication.views import home_redirect
from business_platform.health import (
    health_check, health_db, health_redis,
    health_full, health_ready, health_live, health_apps
)

urlpatterns = [
    # Health Check Endpoints (no authentication required)
    path('health/', health_check, name='health_check'),
    path('health/db/', health_db, name='health_db'),
    path('health/redis/', health_redis, name='health_redis'),
    path('health/full/', health_full, name='health_full'),
    path('health/ready/', health_ready, name='health_ready'),
    path('health/live/', health_live, name='health_live'),
    path('health/apps/', health_apps, name='health_apps'),

    # Admin
    path('admin/', admin.site.urls),

    # Internationalization
    path('i18n/setlang/', set_language, name='set_language'),

    # Authentication
    path('auth/', include('authentication.urls')),

    # Dashboard
    path('', home_redirect, name='home'),  # Smart redirect based on auth status
    path('dashboard/', include('dashboard.urls')),

    # Admin Panel (User & App Management)
    path('admin-panel/', include('admin_panel.urls')),

    # SSO API Endpoints
    path('api/sso/', include('sso.urls')),

    # App Integration - Fixed paths for each business application
    # path('apps/leave/', include('app_integration.urls', namespace='app_leave')),
    # path('apps/quotations/', include('app_integration.urls', namespace='app_quotations')),
    # path('apps/expenses/', include('expense_claims.urls')),  # TODO: Fix expense claims integration
    # path('apps/crm/', include('app_integration.urls', namespace='app_crm')),
    # path('apps/assets/', include('app_integration.urls', namespace='app_assets')),
    # path('apps/stripe/', include('app_integration.urls', namespace='app_stripe')),

    # Expense System Direct Routes
    path('expense-claims/', include('expense_claims.urls')),
    # Redirect legacy /claims/ URLs to /expense-claims/
    re_path(r'^claims/(?P<path>.*)$', RedirectView.as_view(url='/expense-claims/%(path)s', permanent=True)),
    # path('expense-accounts/', include('expense_accounts.urls')),  # Disabled - user model conflict
    path('expense-documents/', include('expense_documents.urls')),
    path('expense-reports/', include('expense_reports.urls')),

    # Quotation System
    path('quotations/', include('quotations.urls')),

    # Asset Tracking System
    path('assets/', include('assets.urls')),
    path('locations/', include('locations.urls')),
    path('movements/', include('movements.urls')),

    # Project & Event Management
    path('project-management/', include('project_management.urls')),
    path('event-management/', include('event_management.urls')),

    # Leave Management System
    path('leave/', include('leave_management.urls')),

    # Attendance Systems
    path('attendance/', include('attendance.urls')),  # Staff daily attendance
    path('qr-attendance/', include('qr_attendance.urls')),  # QR event attendance

    # CRM System
    path('crm/', include('crm.urls')),  # Customer Relationship Management

    # API endpoints (commented out until api module is created)
    # path('api/v1/', include('app_integration.api.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Admin site customization
admin.site.site_header = "Business Platform Administration"
admin.site.site_title = "Business Platform Admin"
admin.site.index_title = "Welcome to Business Platform Administration"