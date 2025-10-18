"""
URL configuration for Integrated Business Platform.

Main hub that provides access to all business applications.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from apps.dashboard.views import home_view

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # Home and Authentication
    path('', home_view, name='home'),
    path('auth/', include('authentication.urls')),

    # Main Dashboard
    path('dashboard/', include('apps.dashboard.urls')),

    # External App Proxies/Links
    # These will redirect or proxy to the actual applications
    # path('expense-claims/', proxy_view('http://localhost:8001')),
    # path('leave/', proxy_view('http://localhost:8002')),
    # path('assets/', proxy_view('http://localhost:8003')),
    # path('crm/', proxy_view('http://localhost:8004')),
    # path('quotations/', proxy_view('http://localhost:8005')),
    # path('stripe/', proxy_view('http://localhost:8081')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Admin site customization
admin.site.site_header = "Business Platform Administration"
admin.site.site_title = "Business Platform Admin"
admin.site.index_title = "Welcome to Business Platform Administration"