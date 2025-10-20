"""URLs for Admin Panel"""

from django.urls import path
from . import views
from . import status_views

app_name = 'admin_panel'

urlpatterns = [
    # Dashboard
    path('', views.admin_dashboard, name='dashboard'),

    # User Management
    path('users/', views.user_list, name='user_list'),
    path('users/<int:user_id>/', views.user_detail, name='user_detail'),
    path('users/<int:user_id>/update-access/', views.update_user_app_access, name='update_user_app_access'),

    # App Access Matrix
    path('app-access-matrix/', views.app_access_matrix, name='app_access_matrix'),
    path('bulk-grant-access/', views.bulk_grant_access, name='bulk_grant_access'),

    # Audit Logs
    path('audit-logs/', views.audit_logs, name='audit_logs'),

    # App Status Dashboard
    path('app-status/', status_views.app_status_dashboard, name='app_status_dashboard'),
    path('app-status/<str:app_code>/', status_views.app_status_detail, name='app_status_detail'),
    path('app-status/<str:app_code>/update/', status_views.update_app_status, name='update_app_status'),

    # Function Status
    path('function-status-board/', status_views.function_status_board, name='function_status_board'),
    path('functions/<int:function_id>/update/', status_views.update_function_status, name='update_function_status'),
    path('blocked-functions/', status_views.blocked_functions_report, name='blocked_functions_report'),

    # Timeline
    path('timeline/', status_views.timeline_view, name='timeline_view'),
]
