"""SSO URL configuration."""
from django.urls import path
from . import views

app_name = 'sso'

urlpatterns = [
    # Token management
    path('token/', views.SSOTokenObtainView.as_view(), name='token_obtain'),
    path('refresh/', views.SSOTokenRefreshView.as_view(), name='token_refresh'),
    path('validate/', views.SSOTokenValidateView.as_view(), name='token_validate'),

    # User information
    path('user/', views.SSOUserInfoView.as_view(), name='user_info'),
    path('check-permission/', views.SSOPermissionCheckView.as_view(), name='check_permission'),

    # Logout
    path('logout/', views.sso_logout, name='logout'),
]
