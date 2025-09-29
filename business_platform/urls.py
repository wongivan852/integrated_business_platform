"""
URL configuration for business_platform project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # Authentication
    path('auth/', include('authentication.urls')),

    # Dashboard
    path('', RedirectView.as_view(url='/auth/login/', permanent=False)),  # Redirect to login
    path('dashboard/', include('dashboard.urls')),

    # App Integration - Fixed paths for each business application
    # path('apps/leave/', include('app_integration.urls', namespace='app_leave')),
    # path('apps/quotations/', include('app_integration.urls', namespace='app_quotations')),
    # path('apps/expenses/', include('expense_claims.urls')),  # TODO: Fix expense claims integration
    # path('apps/crm/', include('app_integration.urls', namespace='app_crm')),
    # path('apps/assets/', include('app_integration.urls', namespace='app_assets')),
    # path('apps/stripe/', include('app_integration.urls', namespace='app_stripe')),

    # Expense System Direct Routes (TODO: Fix URL patterns)
    # path('expense-accounts/', include('expense_accounts.urls')),
    # path('expense-documents/', include('expense_documents.urls')),
    # path('expense-reports/', include('expense_reports.urls')),

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