"""
URL Configuration for Event Management App
"""
from django.urls import path
from . import views

app_name = 'event_management'

urlpatterns = [
    # Event List and Detail
    path('', views.event_list, name='event_list'),
    path('event/<int:pk>/', views.event_detail, name='event_detail'),
    path('event/create/', views.event_create, name='event_create'),
    path('event/<int:pk>/edit/', views.event_edit, name='event_edit'),

    # Dashboard
    path('dashboard/', views.event_dashboard, name='dashboard'),

    # Prerequisites
    path('event/<int:event_pk>/prerequisites/', views.event_prerequisites, name='event_prerequisites'),

    # Costs
    path('event/<int:event_pk>/costs/', views.event_costs, name='event_costs'),

    # Work Logs
    path('event/<int:event_pk>/worklogs/', views.event_worklogs, name='event_worklogs'),

    # Equipment
    path('event/<int:event_pk>/equipment/', views.event_equipment, name='event_equipment'),

    # Approvals
    path('event/<int:event_pk>/approvals/', views.event_approvals, name='event_approvals'),
    path('approval/<int:pk>/review/', views.approval_review, name='approval_review'),

    # Reviews
    path('event/<int:event_pk>/review/', views.event_review_create, name='event_review_create'),

    # Reminders
    path('event/<int:event_pk>/reminders/', views.reminder_list, name='reminder_list'),
    path('event/<int:event_pk>/reminder/create/', views.reminder_create, name='reminder_create'),
    path('reminder/<int:pk>/', views.reminder_detail, name='reminder_detail'),
    path('reminder/<int:pk>/edit/', views.reminder_edit, name='reminder_edit'),
    path('reminder/<int:pk>/delete/', views.reminder_delete, name='reminder_delete'),
    path('reminder/<int:pk>/send/', views.reminder_send_now, name='reminder_send_now'),

    # ========================================
    # Phase 4: Customer Feedback URLs
    # ========================================
    # Public feedback submission (no login required)
    path('feedback/<uuid:token>/', views.customer_feedback_submit, name='customer_feedback_submit'),
    path('feedback/<uuid:token>/thank-you/', views.customer_feedback_thank_you, name='feedback_thank_you'),

    # Staff feedback management
    path('feedback/', views.feedback_list, name='feedback_list'),
    path('feedback/<int:pk>/detail/', views.feedback_detail, name='feedback_detail'),
    path('feedback/<int:pk>/review/', views.feedback_review, name='feedback_review'),
    path('event/<int:event_pk>/feedback/create/', views.feedback_create_for_event, name='feedback_create'),

    # ========================================
    # Phase 4: Equipment Damage Reports
    # ========================================
    path('event/<int:event_pk>/damage-reports/', views.damage_report_list, name='damage_report_list'),
    path('equipment/<int:equipment_pk>/damage/create/', views.damage_report_create, name='damage_report_create'),
    path('damage/<int:pk>/', views.damage_report_detail, name='damage_report_detail'),
    path('damage/<int:pk>/edit/', views.damage_report_edit, name='damage_report_edit'),
    path('damage/<int:report_pk>/photo/upload/', views.damage_photo_upload, name='damage_photo_upload'),
    path('damage-photo/<int:pk>/delete/', views.damage_photo_delete, name='damage_photo_delete'),

    # ========================================
    # Phase 4: Equipment Management
    # ========================================
    path('equipment/<int:pk>/return/', views.equipment_return_process, name='equipment_return'),
    path('event/<int:event_pk>/inventory/', views.equipment_inventory, name='equipment_inventory'),

    # ========================================
    # Phase 4: Analytics
    # ========================================
    path('analytics/', views.analytics_dashboard, name='analytics_dashboard'),
]
