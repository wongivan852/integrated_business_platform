"""
URL configuration for QR code attendance app.
"""

from django.urls import path
from . import views

app_name = 'qr_attendance'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('scanner/', views.scanner, name='scanner'),
    path('participants/', views.participant_list, name='participant_list'),
    path('participants/create/', views.participant_create, name='participant_create'),
    path('participants/<uuid:pk>/', views.participant_detail, name='participant_detail'),
    path('reports/', views.reports, name='reports'),

    # Venue Management
    path('venues/', views.venue_list, name='venue_list'),
    path('venues/create/', views.venue_create, name='venue_create'),
    path('venues/<uuid:pk>/', views.venue_detail, name='venue_detail'),

    # API endpoints
    path('api/scan/', views.scan_qr_code, name='scan_qr_code'),
]
