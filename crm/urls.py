# urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views, frontend_views
# from .monitoring import health_check_view, metrics_view  # Temporarily disabled

# API Routes
router = DefaultRouter()
router.register(r'customers', views.CustomerViewSet)
router.register(r'courses', views.CourseViewSet)
router.register(r'enrollments', views.EnrollmentViewSet)
router.register(r'conferences', views.ConferenceViewSet)
router.register(r'communications', views.CommunicationLogViewSet)

app_name = 'crm'

urlpatterns = [
    # Redirect public routes to secure login-required routes
    path('', frontend_views.dashboard, name='dashboard'),
    path('customers/', frontend_views.customer_list, name='customer_list'),
    path('customers/create/', frontend_views.customer_create, name='customer_create'),
    path('customers/export/csv/', frontend_views.export_customers_csv, name='export_customers_csv'),
    
    # Protected Frontend Routes (require login)
    path('secure/', frontend_views.dashboard, name='secure_dashboard'),
    path('secure/customers/', frontend_views.customer_list, name='secure_customer_list'),
    path('secure/customers/create/', frontend_views.customer_create, name='secure_customer_create'),
    path('secure/customers/<uuid:customer_id>/', frontend_views.customer_detail, name='customer_detail'),
    path('secure/customers/<uuid:customer_id>/edit/', frontend_views.customer_edit, name='customer_edit'),
    path('secure/customers/<uuid:customer_id>/delete/', frontend_views.customer_delete, name='customer_delete'),
    path('secure/customers/<uuid:customer_id>/message/', frontend_views.send_message, name='send_message'),
    
    # Additional secure views
    path('dashboard/', frontend_views.dashboard, name='customer_dashboard'),
    
    # Test endpoints (no security)
    path('test/', views.test_dashboard, name='test_dashboard'),
    path('test/customers/create/', views.test_customer_create, name='test_customer_create'),
    path('test/customers/export/csv/', views.test_export_csv, name='test_export_csv'),
    path('test/country-code/', frontend_views.test_country_code_form, name='test_country_code_form'),
    path('test/youtube/', frontend_views.test_youtube_form, name='test_youtube_form'),
    path('test/simple-youtube/', frontend_views.simple_youtube_test, name='simple_youtube_test'),
    path('test/api-youtube/', frontend_views.api_youtube_test, name='api_youtube_test'),
    
    # API Routes
    path('api/v1/', include(router.urls)),
    path('api-auth/', include('rest_framework.urls')),
    
    # Monitoring endpoints
    # path('health/', health_check_view, name='health_check'),  # Temporarily disabled
    # path('metrics/', metrics_view, name='metrics'),  # Temporarily disabled
]
