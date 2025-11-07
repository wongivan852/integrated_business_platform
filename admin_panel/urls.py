"""
URL configuration for admin_panel app
"""

from django.urls import path
from . import views

app_name = 'admin_panel'

urlpatterns = [
    # Dashboard
    path('', views.admin_dashboard, name='dashboard'),

    # User Management
    path('users/', views.user_list, name='user_list'),
    path('users/<int:user_id>/', views.user_detail, name='user_detail'),

    # App Access Matrix
    path('app-access-matrix/', views.app_access_matrix, name='app_access_matrix'),

    # AJAX API Endpoints
    path('api/users/<int:user_id>/apps/<str:app_name>/toggle/', views.toggle_app_access, name='toggle_app_access'),
    path('api/users/<int:user_id>/grant-all/', views.grant_all_apps_access, name='grant_all_apps'),
    path('api/users/<int:user_id>/revoke-all/', views.revoke_all_apps_access, name='revoke_all_apps'),
]
