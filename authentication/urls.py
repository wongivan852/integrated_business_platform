"""
URL configuration for authentication app.
"""

from django.urls import path
from . import views

app_name = 'authentication'

urlpatterns = [
    # Authentication URLs
    path('login/', views.EmailLoginView.as_view(), name='login'),
    path('logout/', views.EmailLogoutView.as_view(), name='logout'),
    path('register/', views.UserRegistrationView.as_view(), name='register'),
    path('registration-pending/', views.registration_pending, name='registration_pending'),
    path('profile/', views.UserProfileView.as_view(), name='profile'),
    path('refresh-token/', views.refresh_sso_token, name='refresh_token'),
    path('change-password/', views.change_password, name='change_password'),

    # Superadmin approval URLs
    path('pending-approvals/', views.pending_approvals, name='pending_approvals'),
    path('approve-user/<int:user_id>/', views.approve_user, name='approve_user'),
    path('reject-user/<int:user_id>/', views.reject_user, name='reject_user'),

    # SSO API URLs
    path('api/sso/validate/', views.sso_validate_token, name='sso_validate'),
    path('api/sso/user-info/', views.sso_get_user_info, name='sso_user_info'),
    path('api/sso/logout/', views.sso_logout, name='sso_logout'),
]